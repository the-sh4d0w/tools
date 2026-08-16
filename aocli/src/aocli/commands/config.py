"""Configure the tool."""

import rich.box
import rich.table
import rich_click as click

from aocli import CONFIG, CONSOLE


@click.group(context_settings={"show_default": True})
def config() -> None:
    """Configure the tool."""


@config.command(name="list", aliases=["ls"])
def aocli_list() -> None:
    """List all keys and values from the config."""
    table: rich.table.Table = rich.table.Table(
        title="AoCLI config", box=rich.box.MINIMAL_DOUBLE_HEAD, row_styles=["", "dim"])
    table.add_column("key")
    table.add_column("value")
    for key, value in CONFIG:
        table.add_row(key, str(value))
    CONSOLE.print(table)


@config.command()
@click.argument("key", type=str, required=True, help="Key to get the value for.")
def get(key: str) -> None:
    """Get the value for a key in the config."""
    if hasattr(CONFIG, key):
        CONSOLE.print(getattr(CONFIG, key))
    else:
        CONSOLE.print(f"[red]Error[/]: Key [yellow]{key}[/] is not in config.")


@config.command(name="set")
@click.argument("key", type=str, required=True, help="Key to get set value for.")
@click.argument("value", type=str, required=True, help="Value to set.")
def aocli_set(key: str, value: str) -> None:
    """Set the value for a key in the config."""
    if hasattr(CONFIG, key):
        setattr(CONFIG, key, value)
        CONFIG.save()
        CONSOLE.print(f"Set key [yellow]{key}[/] to value [yellow]{value}[/].")
    else:
        CONSOLE.print(f"[red]Error[/]: Key [yellow]{key}[/] is not in config.")
