"""Manage Advent of Code puzzles."""

import importlib.metadata

import rich_click as click

from aocli import PROJECT_NAME, CONFIG
from aocli.commands import config
from aocli.commands import setup
from aocli.commands import submit


def project_version(project_name: str) -> str | None:
    """Get the project version."""
    try:
        return importlib.metadata.version(project_name)
    except importlib.metadata.PackageNotFoundError:
        return None


@click.group(epilog=f"Session cookie is expected to be in the file '{CONFIG.session_path}'.",
             context_settings={"show_default": True})
@click.version_option(version=project_version(PROJECT_NAME), prog_name=PROJECT_NAME)
def main() -> None:
    """Manage Advent of Code puzzles."""


main.add_command(setup.setup)
main.add_command(config.config)
main.add_command(submit.submit)
