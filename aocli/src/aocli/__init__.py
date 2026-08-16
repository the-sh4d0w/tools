"""Shared stuff."""

import datetime
import pathlib

import rich.console

from aocli import models


PROJECT_NAME = "aocli"
TODAY = datetime.date.today()
DIRECTORY_PATH = pathlib.Path(__file__).parent
CONFIG = models.Config.load(DIRECTORY_PATH.joinpath("config.json"))
PLACEHOLDER_PATH = DIRECTORY_PATH.joinpath(CONFIG.placeholders_path)
CONSOLE = rich.console.Console(highlight=False)
AOC_DOMAIN = f"https://{CONFIG.domain.replace("https://", "").replace("http://", "")}"
