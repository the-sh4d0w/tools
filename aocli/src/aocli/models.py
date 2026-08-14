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
    session_path: pathlib.Path
    user_agent: str
    code_placeholders: list[CodePlaceholder]
