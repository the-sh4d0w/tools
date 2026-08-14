"""Manage Advent of Code puzzles."""

import datetime
import importlib.metadata
import pathlib
import sys
import time
import typing

import bs4
import rich_click as click
import requests
import rich.console

from aocli import models


PROJECT_NAME = "aocli"
TODAY = datetime.date.today()
DIRECTORY_PATH = pathlib.Path(__file__).parent
CONFIG = models.Config.model_validate_json(
    DIRECTORY_PATH.joinpath("config.json").read_text(encoding="utf-8"))
CONSOLE = rich.console.Console(highlight=False)


def project_version(project_name: str) -> str | None:
    """Get the project version."""
    try:
        return importlib.metadata.version(project_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def get_code_placeholder(language: str) -> str:
    """Get code placeholder for language.

    Arguments:
        - langage: programming language.

    Returns:
        Code placeholder.
    """
    for placeholder in CONFIG.code_placeholders:
        if placeholder.language == language:
            return placeholder.code
    # this can't be reached
    return ""


@click.group(epilog=f"Session cookie is expected to be in the file '{CONFIG.session_path}'.",
             context_settings={"show_default": True})
@click.version_option(version=project_version(PROJECT_NAME), prog_name=PROJECT_NAME)
def main() -> None:
    """Manage Advent of Code puzzles."""


# FIXME: won't work out of season because of the default values; make reasonable choices (or today)
# -> highest available year
# -> lowest (available) day that is not yet created
# FIXME: force option
@main.command()
@click.option("-d", "--day", type=click.IntRange(0, 25), default=TODAY.day,
              help="Day of advent of code.")
@click.option("-y", "--year", type=click.IntRange(
    2015, TODAY.year if TODAY.month == 12 else TODAY.year - 1), default=TODAY.year,
    help="Year of advent of code.")
@click.option("-p", "--part", type=click.IntRange(1, 2), default=1, help="Part of the task.")
@click.option("-l", "--language", type=click.Choice([p.language for p in CONFIG.code_placeholders],
                                                    case_sensitive=False), default="python",
              help="Programming language.")
@click.option("-w", "--wait", is_flag=True, help="Wait until task is available.")
@click.option("-n", "--notify", is_flag=True, help="Send ntfy notification when finished.")
@click.option("--ntfy_url", type=str, show_default=True, default="http://olympus:1234/aoc",
              help="URL for ntfy.")
def setup(day: int, year: int, part: int, language: str, wait: bool, notify: bool, ntfy_url: str) \
        -> None:
    """Automatically download files and set up folder and files for a day of advent of code."""
    # wait until release of task; +30 seconds to prevent bug
    if wait and datetime.datetime(year, 12, day, 6) > datetime.datetime.now():
        with CONSOLE.status(
            "Waiting until task releases at [blue]"
                f"{datetime.datetime(year, 12, day, 6).astimezone().isoformat()}[/]..."):
            time.sleep((datetime.datetime(year, 12, day, 6)
                        - datetime.datetime.now()).total_seconds() + 30)
    url = f"https://{CONFIG.domain}/{year}/day/{day}"
    file = pathlib.Path(CONFIG.session_path)

    # exit if session cookie file doesn't exist
    if not file.exists():
        CONSOLE.print(f"[red]Error[/]: the file '{CONFIG.session_path}' "
                      "does not exist.")
        return

    # get session token
    session = file.read_text(encoding="utf-8").strip()

    try:
        start_time = time.monotonic()
        with CONSOLE.status(f"Downloading AoC day {day:02}..."):
            # download example(s) and input
            with requests.Session() as sess:
                # set session token
                sess.cookies.set(name="session", value=session,
                                 domain=CONFIG.domain)
                response = sess.get(url)
                match response.status_code:
                    case 200:
                        pass
                    case _:
                        raise FileNotFoundError
        CONSOLE.print(f"Downloaded AoC day {day:02} "
                      f"in {time.monotonic() - start_time:.2}s.")
    except FileNotFoundError:
        CONSOLE.print(f"[red]Error[/]: day {day} "
                      "is not (yet) available.")
        sys.exit(-1)

    start_time = time.monotonic()
    with CONSOLE.status(f"Parsing AoC day {day:02}..."):
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        title = typing.cast(bs4.Tag, soup.find(
            "h2")).text.replace("-", "").strip()
        examples = [typing.cast(bs4.Tag, pre.find("code")).text.strip()
                    for pre in soup.find_all("pre")]
        input_text = sess.get(f"{url}/input").text.strip()

        # exit with error if part two not available
        if part == 2 and not "Part Two" in response.text:
            CONSOLE.print(
                "[red]Error[/]: part two is not yet available.")
            sys.exit(-1)
        CONSOLE.print(
            f"Parsed Aoc day {day:02} in {time.monotonic() - start_time:.2}s.")

    start_time = time.monotonic()
    with CONSOLE.status("Creating folders and files..."):
        # setup folder and files
        format_values: dict[str, str | int] = {
            "title": title,
            "url": url + ("#part2" if part == 2 else ""),
            "part_word": "one" if part == 1 else "two",
            "day": day,
            "part": part
        }
        pathlib.Path(f"{day:02}").mkdir(exist_ok=True)
        pathlib.Path(f"{day:02}/puzzle{day:02}_{part}.py").write_text(
            data=get_code_placeholder(language).format_map(format_values), encoding="utf-8")
        pathlib.Path(f"{day:02}/example{day:02}_{part}.txt").write_text(
            data=examples[part - 1 if len(examples) != 1 else 0], encoding="utf-8")
        pathlib.Path(f"{day:02}/input{day:02}.txt").write_text(
            data=input_text, encoding="utf-8")
    CONSOLE.print(
        f"Created folders and files in {time.monotonic() - start_time:.2}s.")

    # send notification
    if notify:
        CONSOLE.print("Sending notification...")
        requests.post(ntfy_url, timeout=10,
                      data=f"Part {part} of {year}-12-{day:02} finished downloading.",
                      headers={"Title": "Advent of Code Setup", "Tags": "christmas_tree"})
