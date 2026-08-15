"""Shared stuff."""

import datetime
import pathlib

import rich.console

from aocli import models


PROJECT_NAME = "aocli"
TODAY = datetime.date.today()
DIRECTORY_PATH = pathlib.Path(__file__).parent
CONFIG = models.Config.model_validate_json(
    DIRECTORY_PATH.joinpath("config.json").read_text(encoding="utf-8"))
PLACEHOLDER_PATH = DIRECTORY_PATH.joinpath(CONFIG.placeholders_path)
CONSOLE = rich.console.Console(highlight=False)
