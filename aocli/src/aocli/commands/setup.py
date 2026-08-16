"""Set up a day of Advent of Code."""

import datetime
import pathlib
import sys
import time
import typing

import bs4
import jinja2
import rich_click as click
import requests

from aocli import TODAY, CONFIG, CONSOLE, PLACEHOLDER_PATH, AOC_DOMAIN


class DayNotAvailableError(Exception):
    """Day not available error."""


@click.command()
@click.option("--day", "-d", type=click.IntRange(0, 25), default=TODAY.day,
              help="Day of Advent of Code.")
@click.option("--year", "-y", type=click.IntRange(2015, TODAY.year), default=TODAY.year,
              help="Year of Advent of Code.")
@click.option("--part", "-p", type=click.IntRange(1, 2), default=1, help="Part of the task.")
@click.option("--language", "-l", type=click.Choice([f.stem for f in PLACEHOLDER_PATH.iterdir()],
                                                    case_sensitive=False), default="python",
              help="Programming language for placeholder.")
@click.option("--wait", "-w", is_flag=True, help="Wait until task is available.")
@click.option("--notify", "-n", is_flag=True, help="Send ntfy (https://ntfy.sh) notification when finished.")
@click.option("--ntfy_url", type=str, show_default=True, default="http://olympus:1234/aoc",
              help="URL for ntfy.")
@click.option("--force", "-f", is_flag=True, help="Force overwriting of output.")
def setup(day: int, year: int, part: int, language: str, wait: bool, notify: bool, ntfy_url: str,
          force: str) -> None:
    """Set up a day of Advent of Code.

    Automatically download example and input and create folder and placeholder file for a puzzle.

    Default values for day and year are taken from today's date.
    """
    # wait until release of task; +30 seconds to prevent bug
    if wait and datetime.datetime(year, 12, day, 6) > datetime.datetime.now():
        with CONSOLE.status(
            "Waiting until task releases at [blue]"
                f"{datetime.datetime(year, 12, day, 6).astimezone().isoformat()}[/]..."):
            time.sleep((datetime.datetime(year, 12, day, 6)
                        - datetime.datetime.now()).total_seconds() + 30)

    # check if session file exists
    if not (session_file := pathlib.Path(CONFIG.session_path)).exists():
        CONSOLE.print(f"[red]Error[/]: The file '{CONFIG.session_path}' "
                      "does not exist.")
        sys.exit(1)
    # get session token
    session = session_file.read_text(encoding="utf-8").strip()

    try:
        start_time = time.monotonic()
        with CONSOLE.status(f"Downloading AoC day {day:02}..."):
            # download example(s) and input
            with requests.Session() as sess:
                # set session token
                sess.cookies.set(name="session", value=session,
                                 domain=CONFIG.domain)
                response: requests.Response = sess.get(
                    url=f"{AOC_DOMAIN}/{year}/day/{day}",
                    headers={"User-Agent": CONFIG.user_agent})
                match response.status_code:
                    case 200:
                        pass
                    case _:
                        raise DayNotAvailableError
        CONSOLE.print(f"Downloaded AoC day {day:02} "
                      f"in {time.monotonic() - start_time:.2}s.")
    except DayNotAvailableError:
        CONSOLE.print(f"[red]Error[/]: Day {day} is not (yet) available.")
        if year >= 2025 and day > 12:
            CONSOLE.print("[cyan]Hint[/]: Since 2025 only 12 days are "
                          "available (https://adventofcode.com/about#faq_num_days).")
        sys.exit(1)

    start_time = time.monotonic()
    with CONSOLE.status(f"Parsing AoC day {day:02}..."):
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        title = typing.cast(bs4.Tag, soup.find(
            "h2")).text.replace("-", "").strip()
        examples = [typing.cast(bs4.Tag, pre.find("code")).text.strip()
                    for pre in soup.find_all("pre")]
        input_text = sess.get(f"{AOC_DOMAIN}/input").text.strip()

        # exit with error if part two is not available
        if part == 2 and not "Part Two" in response.text:
            CONSOLE.print("[red]Error[/]: Part two is not yet available.")
            sys.exit(1)
        CONSOLE.print("Parsed Aoc day "
                      f"{day:02} in {time.monotonic() - start_time:.2}s.")

    start_time = time.monotonic()
    with CONSOLE.status("Creating folders and files..."):
        # setup folder and files
        format_values: dict[str, str | int] = {
            "title": title,
            "url": AOC_DOMAIN + ("#part2" if part == 2 else ""),
            "part_word": "one" if part == 1 else "two",
            "day": f"{day:02}",
            "part": part
        }
        environment: jinja2.Environment = jinja2.Environment(loader=jinja2.FileSystemLoader(
            PLACEHOLDER_PATH, encoding="utf-8"), keep_trailing_newline=True)
        puzzle_text: str = environment.get_template(
            f"{language}.j2").render(format_values)
        pathlib.Path(f"{day:02}").mkdir(exist_ok=True)
        # check if (relevant) files already exists or if we want to override
        puzzle_file = pathlib.Path(f"{day:02}/puzzle{day:02}_{part}.py")
        example_file = pathlib.Path(f"{day:02}/example{day:02}_{part}.txt")
        if (not puzzle_file.exists() and not example_file.exists()) or force:
            puzzle_file.write_text(puzzle_text, encoding="utf-8")
            example_file.write_text(data=examples[part - 1 if len(examples) != 1 else 0],
                                    encoding="utf-8")
            pathlib.Path(f"{day:02}/input{day:02}.txt").write_text(data=input_text,
                                                                   encoding="utf-8")
            CONSOLE.print("Created folders and files in "
                          f"{time.monotonic() - start_time:.2}s.")
        else:
            CONSOLE.print(f"[red]Error[/]: File(s) {puzzle_file} and/or {example_file} "
                          "already exist(s).")
            sys.exit(1)

    # send notification
    if notify:
        try:
            response: requests.Response = requests.post(
                ntfy_url, timeout=10,
                data=f"Part {part} of {year}-12-{day:02} finished downloading.",
                headers={"Title": "Advent of Code Setup (AoCLI)", "Tags": "christmas_tree"})
            # check if notification was sent successfully
            assert response.status_code == 200 \
                and response.json()["event"] == "message"
            CONSOLE.print("Sent notification.")
        except requests.RequestException, AssertionError:
            CONSOLE.print("[red]Error[/]: Notification could not be sent.")
            sys.exit(1)
