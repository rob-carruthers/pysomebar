"""Modules."""

from .battery import BatteryModule
from .brightness import BrightnessModule
from .date import DateModule
from .module import Module
from .pacman import PacmanModule
from .portage import PortageModule
from .pulse import PulseModule
from .temp import TempModule

__all__ = [
    "BatteryModule",
    "BrightnessModule",
    "DateModule",
    "Module",
    "PacmanModule",
    "PortageModule",
    "PulseModule",
    "TempModule",
]
