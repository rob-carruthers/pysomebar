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
    interval: int = 5


class BatteryModuleConfig(ModuleConfig):
    """Config for battery module."""


class BrightnessModuleConfig(ModuleConfig):
    """Config for brightness module."""

    device: str | None = None


class DateModuleConfig(ModuleConfig):
    """Config for the date/time module.

    Attributes
    ----------
    format : str, default "%d/%m/%Y %H:%M"
        Format to pass to strftime.

    """

    format: str = "%d/%m/%Y %H:%M"


class PulseModuleConfig(ModuleConfig):
    """Config for pulse module."""


class TempModuleConfig(ModuleConfig):
    """Config for temp module."""

    device: str | None = None


class Config(BaseModel):
    """Top-level config."""

    battery: BatteryModuleConfig = BatteryModuleConfig()
    brightness: BrightnessModuleConfig = BrightnessModuleConfig()
    date: DateModuleConfig = DateModuleConfig()
    pulse: PulseModuleConfig = PulseModuleConfig()
    temp: TempModuleConfig = TempModuleConfig()


try:
    with Path(CONFIG_FILE).open("rb") as f:
        data = tomllib.load(f)

    CONFIG = Config(**data)

except FileNotFoundError:
    CONFIG = Config()
