"""Configuration."""

import tomllib
from pathlib import Path

from pydantic import BaseModel

CONFIG_FILE = "./config.toml"


class ModuleConfig(BaseModel):
    """Config for a module.

    Attributes
    ----------
    enabled : bool, default False
        Whether a module should be enabled.

    """

    enabled: bool = False


class DateModuleConfig(ModuleConfig):
    format: str


class Config(BaseModel):
    date: DateModuleConfig


with Path(CONFIG_FILE).open("rb") as f:
    data = tomllib.load(f)

CONFIG = Config(**data)
