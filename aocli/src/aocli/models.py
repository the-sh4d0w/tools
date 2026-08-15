"""Pydantic models."""

import pathlib

import pydantic


class CodePlaceholder(pydantic.BaseModel):
    """Model for code placeholder."""
    language: str
    code: str


class Config(pydantic.BaseModel):
    """Model for config."""
    domain: str
    user_agent: str
    session_path: pathlib.Path
    placeholders_path: pathlib.Path
