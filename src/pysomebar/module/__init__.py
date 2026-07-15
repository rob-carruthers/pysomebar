"""Modules."""

from .battery import BatteryModule
from .brightness import BrightnessModule
from .cpu import CPUModule
from .date import DateModule
from .memory import MemoryModule
from .module import Module
from .mpd import MPDModule
from .network import NetworkModule
from .pacman import PacmanModule
from .portage import PortageModule
from .pulse import PulseModule
from .temp import TempModule

__all__ = [
    "BatteryModule",
    "BrightnessModule",
    "CPUModule",
    "DateModule",
    "MPDModule",
    "MemoryModule",
    "Module",
    "NetworkModule",
    "PacmanModule",
    "PortageModule",
    "PulseModule",
    "TempModule",
]
