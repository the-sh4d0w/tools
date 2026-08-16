"""Submit a puzzle answer."""

import pathlib
import sys

import requests
import rich_click as click

from aocli import CONFIG, CONSOLE, AOC_DOMAIN


@click.command()
@click.argument("year", type=int, required=True, help="Year to submit for.")
@click.argument("day", type=int, required=True, help="Day to submit for.")
@click.argument("part", type=click.IntRange(1, 2), required=True, help="Part to submit for.")
@click.argument("answer", type=str, required=True, help="Answer to submit.")
def submit(year: int, day: int, part: int, answer: str) -> None:
    """Submit a puzzle answer."""
    file = pathlib.Path(CONFIG.session_path)
    # exit if session cookie file doesn't exist
    if not file.exists():
        CONSOLE.print(f"[red]Error[/]: The file '{CONFIG.session_path}' "
                      "does not exist.")
        sys.exit(1)
    # get session token
    session = file.read_text(encoding="utf-8").strip()

    with requests.Session() as sess:
        # set session token
        sess.cookies.set(name="session", value=session,
                         domain=CONFIG.domain)
        response: requests.Response = sess.post(
            url=f"{AOC_DOMAIN}/{year}/day/{day}/answer",
            headers={"User-Agent": CONFIG.user_agent},
            data={"answer": answer, "level": str(part)})

    # figure out if the answer wa correct; it works...
    if "already complete it" in response.text:
        # already completed
        CONSOLE.print("Answer couldn't be submitted as puzzle has already "
                      "been completed.")
    elif "answer too recently" in response.text:
        # general timeout
        CONSOLE.print("Answer couldn't be submitted as answer was given too recently. "
                      "Wait 5-10 minutes.")
    elif "have guessed incorrectly" in response.text:
        # x wrong attempts timeout
        CONSOLE.print("Answer was [red]wrong[/] and timeout has been applied as "
                      "too many wrong answers have been submitted. Wait 5-10 minutes.")
    elif "not the right answer" in response.text:
        # wrong answer
        CONSOLE.print("Answer was [red]wrong[/].")
    else:
        # hopefully correct answer
        CONSOLE.print("Answer was [green]correct[/].")
