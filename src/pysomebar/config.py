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
    """Config for the date/time module.

    Attributes
    ----------
    format : str, default "%d/%m/%Y %H:%M"
        Format to pass to strftime.

    """

    format: str = "%d/%m/%Y %H:%M"


class Config(BaseModel):
    """Top-level config."""

    date: DateModuleConfig = DateModuleConfig()


try:
    with Path(CONFIG_FILE).open("rb") as f:
        data = tomllib.load(f)

    CONFIG = Config(**data)

except FileNotFoundError:
    CONFIG = Config()
