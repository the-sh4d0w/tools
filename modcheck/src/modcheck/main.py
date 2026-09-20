"""Check if mods in a Modrinth collection is available for a version of Minecraft."""

import importlib.metadata
import typing

import bs4
import click
import requests
import rich.console
import rich.progress


PROJECT_NAME = "modcheck"


def project_version(project_name: str) -> str | None:
    """Get the project version."""
    try:
        return importlib.metadata.version(project_name)
    except importlib.metadata.PackageNotFoundError:
        return None


@click.command()
@click.version_option(version=project_version(PROJECT_NAME), prog_name=PROJECT_NAME)
@click.option("--loader", "-l", type=str, help="Mod loader to check for.")
@click.argument("collection", type=str, help="ID of the Modrinth collection.")
@click.argument("mc-version", type=str, help="The Minecraft version ro check for.")
def main(collection: str, mc_version: str, loader: typing.Optional[str]) -> None:
    """Check if mods in a Modrinth collection is available for a version of Minecraft."""
    console: rich.console.Console = rich.console.Console(highlight=False)
    available_count: int = 0

    # get collection website and parse
    content: str = requests.get(f"https://modrinth.com/collection/{collection}",
                                timeout=10).text
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(content,
                                                features="html.parser")
    collection_title: str = typing.cast(bs4.Tag, soup.select_one("h1")).text
    mod_amount: int = int(typing.cast(bs4.Tag,
                                      soup.select_one("span > span > span")).text)
    console.print(f"Collection [green]{collection_title}[/] contains "
                  f"[yellow]{mod_amount}[/] mods.")

    # iterate through mods and get API info
    for mod_link in rich.progress.track(soup.select(
            "div > a.rounded-xl.no-outline.no-click-animation.custom-focus-indicator"),
            description=f"Checking if mods are available for [yellow]{mc_version}[/]...",
            transient=True, console=console):
        mod_slug: str = typing.cast(str, mod_link.get("href")).split("/")[-1]
        data = requests.get(f"https://api.modrinth.com/v2/project/{mod_slug}",
                            timeout=10).json()
        available: bool = mc_version in data["game_versions"] \
            and (loader is None or loader in data["loaders"])
        status: str = "✔" if available else "❌"
        available_count += available
        console.print(f"[blue]{data["title"]}[/]"
                      f"{status:>{(console.width-len(data["title"])-1)}}")

    loader_text: str = "" if loader is None else f" and loader [bright_cyan]{loader}[/]"
    console.print(f"[yellow]{available_count}[/] of [yellow]{mod_amount}[/] mods "
                  f"([green]{available_count/mod_amount:.0%}[/]) are available for "
                  f"Minecraft version [green]{mc_version}[/]"
                  f"{loader_text}.")
