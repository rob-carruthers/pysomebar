"""Configuration."""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from xdg_base_dirs import xdg_config_home

xdg_config = xdg_config_home() / "pysomebar" / "config.toml"

CONFIG_FILE = xdg_config.resolve() if xdg_config.exists() else Path("./config.toml")

BarType = Literal["somebar", "dwlb"]


class ModuleConfig(BaseModel):
    """Config for a module."""

    interval: int = 5


class MemoryModuleConfig(ModuleConfig):
    """Config for memory module.

    Currently no additonal options.
    """


class CPUModuleConfig(ModuleConfig):
    """Config for CPU module.

    Attributes
    ----------
    yellow_threshold : int, default 60
        Display status as yellow >= `yellow_threshold`.
    red_threshold : int, default 75
        Display status as red >= `red_threshold`.

    """

    yellow_threshold: int = 50
    red_threshold: int = 75


class BatteryModuleConfig(ModuleConfig):
    """Config for battery module.

    Attributes
    ----------
    green_threshold : int, default 30
        Display status as green >= `green_threshold`.
    yellow_threshold : int, default 20
        Display status as yellow >= `yellow_threshold`.

    """

    green_threshold: int = 30
    yellow_threshold: int = 20


class BrightnessModuleConfig(ModuleConfig):
    """Config for brightness module."""

    device: str | None = None


class NetworkModuleConfig(ModuleConfig):
    """Config for network module.

    Attributes
    ----------
    device : str | None, default None
        Network device to return rates from. If `None`, use totals for all interfaces.
    padding : int, default 8
        Number of characters with which to justify using whitespace to avoid excess movement.
    gate : int, default 0
        Number of bytes below which rate is reported as '0', to avoid distaction.

    """

    device: str | None = None
    padding: int = 8
    gate: int = 0


class DateModuleConfig(ModuleConfig):
    """Config for the date/time module.

    Attributes
    ----------
    format : str, default "%d/%m/%Y %H:%M"
        Format to pass to strftime.

    """

    format: str = "%d/%m/%Y %H:%M"


class PacmanModuleConfig(ModuleConfig):
    """Config for pulse module."""

    available_updates_color: str = "white"


class PortageModuleConfig(ModuleConfig):
    """Config for pulse module."""

    watch_file: Path = Path("/var/cache/eix/portage.eix")
    available_updates_color: str = "white"


class PulseModuleConfig(ModuleConfig):
    """Config for pulse module."""

    mute_color: str = "white"


class MPDModuleConfig(ModuleConfig):
    """Config for MPD module."""

    host: str = "localhost"
    port: int = 6600


class TempModuleConfig(ModuleConfig):
    """Config for temp module.

    Attributes
    ----------
    yellow_threshold : int, default 60
        Display status as yellow >= `yellow_threshold`.
    red_threshold : int, default 75
        Display status as red >= `red_threshold`.

    """

    device: str | None = None
    yellow_threshold: int = 60
    red_threshold: int = 75


class Config(BaseModel):
    """Top-level config."""

    bar_type: BarType = "somebar"
    modules: list[str] = ["date"]
    base_color: str = "#ffffff"
    separator: str = " | "
    separator_color: str = "#ffffff"
    edge_padding: int = 0
    colors: dict[str, str] = {"white": "#ffffff"}
    try_reconnect_interval: float = 0.5
    battery: BatteryModuleConfig = BatteryModuleConfig()
    memory: MemoryModuleConfig = MemoryModuleConfig()
    cpu: CPUModuleConfig = CPUModuleConfig()
    brightness: BrightnessModuleConfig = BrightnessModuleConfig()
    network: NetworkModuleConfig = NetworkModuleConfig()
    date: DateModuleConfig = DateModuleConfig()
    pulse: PulseModuleConfig = PulseModuleConfig()
    mpd: MPDModuleConfig = MPDModuleConfig()
    pacman: PacmanModuleConfig = PacmanModuleConfig()
    portage: PortageModuleConfig = PortageModuleConfig()
    temp: TempModuleConfig = TempModuleConfig()


try:
    with CONFIG_FILE.open("rb") as f:
        data = tomllib.load(f)

    CONFIG = Config(**data)

except FileNotFoundError:
    CONFIG = Config()
