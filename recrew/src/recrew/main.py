"""Analyse 'The Crew: Mission Deep Sea' games from BGA."""

import enum
import importlib.metadata
import typing

import bs4
import rich_click as click
import pydantic
import rich
import rich.progress
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


URL_BGA_TABLE: str = "https://de.boardgamearena.com/table?table="

# TODO: analyse (probable) player hands
# TODO: get missions
# TODO: analyse missions (and maybe suggest move)
# TODO: probablym make everything wait until available


class CardColour(enum.StrEnum):
    """The Crew card colours."""
    BLUE = "Blue"  # 1
    GREEN = "Green"  # 2
    PINK = "Pink"  # 3
    YELLOW = "Yellow"  # 4
    SUBMARINE = "Submarine"  # 5


class Card(pydantic.BaseModel):
    """The Crew card."""
    value: int
    colour: CardColour

    @pydantic.field_validator("colour", mode="before")
    @classmethod
    def parse_colour(cls, value: str) -> str:
        """Pre-validate to parse colour if given as integer."""
        if value.isdigit():
            return CardColour({1: "Blue", 2: "Green", 3: "Pink",
                               4: "Yellow", 5: "Submarine"}[int(value)])
        return CardColour(value)

    def __repr__(self) -> str:
        """Get formal string representation for rich."""
        colour_map: dict[CardColour, str] = {
            CardColour.BLUE: "white on blue", CardColour.GREEN: "white on green",
            CardColour.PINK: "white on pink", CardColour.YELLOW: "white on yellow",
            CardColour.SUBMARINE: "white on black"
        }
        return f"[{colour_map[self.colour]}]{self.value}[/]"


class Play(pydantic.BaseModel):
    """The Crew play."""
    player: str
    card: Card


class Trick(pydantic.BaseModel):
    """The Crew trick."""
    winner: str | None = None
    first: str | None = None
    colour: CardColour | None = None
    plays: list[Play] = []


def project_version() -> str | None:
    """Get project version."""
    try:
        return importlib.metadata.version("recrew")
    except importlib.metadata.PackageNotFoundError:
        return None


@click.command()
@click.version_option(version=project_version(), prog_name="recrew")
@click.argument("table-id", type=int, required=True, help="Id of the BGA table.")
@click.option("--player", "-p", type=str, help="BGA username of the player.")
@click.option("--card", "-c", type=str, multiple=True, help="Cards in hand of player.")
@click.option("--login", "-l", is_flag=True, help="Login to BGA to get hand cards of player.")
def main(table_id: int, player: str, card: tuple[str], login: bool) -> None:
    """Read the log of a game of The Crew on BGA and extract as much information as possible.
    """
    # TODO: parse cards if supplied
    cards: list[Card] = []

    # set up selenium driver
    options: Options = Options()
    options.add_argument("--headless=new")
    driver: webdriver.Firefox = webdriver.Firefox(  # pylint: disable=not-callable
        options=options)

    try:
        # got to game overview page
        driver.get(URL_BGA_TABLE + str(table_id))
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.ID, "didomi-notice-disagree-button"))).click()

        # do nothing if game ended already
        if "beendet" in driver.find_element(by=By.ID, value="status_detailled").text:
            rich.print("[red]Table is closed.[/]")
            driver.close()
            return

        # do login if login option is set to be able to get player cards later
        if login:
            # get player name and password
            if not player:
                player = click.prompt(text="Username",  type=str)
            password = click.prompt(
                text="Password", hide_input=True, type=str)

            # do the whole login thing
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[2]/div[1]/div/div[1]/div[8]/a"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[9]/div/div[2]/div/div/div[3]/div/div[2]/div"
                    "/div[2]/div[1]/div/div[2]/form/div[2]/div/div/input"))).send_keys(player)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[9]/div/div[2]/div/div/div[3]/div/div[2]/div"
                    "/div[2]/div[1]/div/div[2]/form/div[3]/div/a"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[9]/div/div[2]/div/div/div[3]/div/div[2]/div"
                    "/div[2]/div[2]/div/form/div[1]/div[2]/div/input"))).send_keys(password)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[9]/div/div[2]/div/div/div[3]/div/div[2]/div"
                    "/div[2]/div[2]/div/form/div[3]/div/div/a"))).click()

            try:
                # try to press the continue buton; this works as a check if the login was successful
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[9]/div/div[2]/div/div/div[3]/div/div[2]/div"
                     "/div[2]/div[3]/div[2]/div[3]/div[3]/div/div/a"))).click()
            except:  # pylint: disable=bare-except
                rich.print("[red]Login failed.[/]")
                driver.close()
                return
            rich.print("[green]Successfully logged in.[/]")

        # got to game page
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "access_game_normal"))).click()

        # close annoying pop-up
        driver.refresh()
        driver.switch_to.frame(driver.find_element(
            by=By.ID, value="gameIframe"))
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "popin_showTour_close"))).click()
        content: str = driver.page_source

        # we have all the data we need; close driver
        driver.close()

        # parse and get players
        soup: bs4.BeautifulSoup = bs4.BeautifulSoup(
            markup=content, features="html.parser")
        players: list[str] = [player.text.strip()
                              for player in soup.select("div.player-name")]

        # analyse logs
        tricks: list[Trick] = []
        logs = typing.cast(bs4.Tag, soup.select_one("div#logs"))
        logs_replayable = logs.find_all("div", class_="log_replayable")
        round_start = [log for log in logs_replayable
                       if "notif_startNewMission" in log.attrs.get("class", "")][0]
        trick: Trick = Trick()
        for log in rich.progress.track(logs_replayable[(logs_replayable.index(round_start))::-1],
                                       description="Processing logs..."):
            if log.has_attr("data-move-id") and (log_entry := log.select_one("div.roundedbox")):
                log_attrs = log.attrs.get("class", "")
                if "notif_startNewMission" in log_attrs:
                    # mission start
                    rich.print("Started mission:", log_entry.text.split()[-1])
                elif "notif_captain" in log_attrs:
                    # captain
                    if playername := log_entry.select_one("span.playername"):
                        rich.print(f"Captain: {playername.text}")
                elif "notif_playCard" in log_attrs:
                    # card played
                    if (playername := log_entry.select_one("span.playername")) and \
                        (card_value := log_entry.select_one("span.card-value")) and \
                            (card_colour := log_entry.select_one("span.logicon")):
                        play: Play = Play(player=playername.text, card=Card(
                            value=int(card_value.text), colour=typing.cast(
                                CardColour, card_colour.attrs["title"])))
                        if trick.first is None and trick.colour is None:
                            trick.first = play.player
                            trick.colour = play.card.colour
                        trick.plays.append(play)
                elif "notif_trickWin" in log_attrs:
                    # trick won
                    if (playername := log_entry.select_one("span.playername")):
                        trick.winner = playername.text
                        tricks.append(trick)
                        trick = Trick()

        # get hand colours if logged in as player
        if login:
            cards = []
            for hand_card in soup.find_all("div", class_="crewds-card selectable"):
                cards.append(Card(value=typing.cast(int, hand_card.attrs["data-value"]),
                                  colour=typing.cast(CardColour, hand_card.attrs["data-color"])))

        # do analysis for missing colours and played cards per colour
        player_colours_missing: dict[str, set[CardColour]] = {
            player: set() for player in players}
        cards_colours_played: dict[CardColour, list[int]] = {
            colour: [] for colour in CardColour}
        for trick in tricks:
            for play in trick.plays:
                if play.card.colour != trick.colour:
                    player_colours_missing[play.player].add(
                        typing.cast(CardColour, trick.colour))
                cards_colours_played[play.card.colour].append(play.card.value)

        # output missing colours
        for player_name in player_colours_missing:
            if len(player_colours_missing[player_name]):
                rich.print(f"{player_name} doesn't have cards of the colours:",
                           ", ".join(player_colours_missing[player_name]))

        # output played cards per colour
        for colour in cards_colours_played:
            if len(cards_colours_played[colour]) > 0:
                rich.print(f"Cards of colour {colour} played:",
                           ", ".join(map(str, sorted(cards_colours_played[colour]))))

        rich.print(f"{player}: {cards}")
    except:  # pylint: disable=bare-except
        rich.print("[red]An error occurred.[/]")
    finally:
        driver.quit()
