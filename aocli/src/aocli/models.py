"""Pydantic models."""

import pathlib

import pydantic


class Config(pydantic.BaseModel):
    """Model for config."""
    __path__: pathlib.Path | str | None = None
    domain: str
    user_agent: str
    session_path: pathlib.Path
    placeholders_path: pathlib.Path

    @classmethod
    def load(cls, path: pathlib.Path | str | None = None) -> Config:
        """Load the config from file."""
        if path is None:
            if Config.__path__ is None:
                # better than nothing; we shouldn't ever be able to reach this anyway
                path = "config.json"
            else:
                path = Config.__path__
        Config.__path__ = path
        return Config.model_validate_json(pathlib.Path(path).read_text(encoding="utf-8"))

    def save(self) -> None:
        """Save the config to file."""
        if Config.__path__ is None:
            # better than nothing; we shouldn't ever be able to reach this anyway
            Config.__path__ = "config.json"
        pathlib.Path(Config.__path__).write_text(
            self.model_dump_json(indent=4), encoding="utf-8")
