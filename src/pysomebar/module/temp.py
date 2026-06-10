"""Temp module for pysomebar."""

from types import MappingProxyType

import psutil

from pysomebar.config import CONFIG

from .module import Module


def convert_time(seconds: int) -> str:
    """Convert seconds to a formatting string of {hours}:{minutes}:{seconds}."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"


class TempModule(Module):
    """Module for showing temps."""

    thresholds = MappingProxyType({75: "", 60: "", 50: "", -274: ""})

    def __init__(self) -> None:  # noqa: D107
        super().__init__(CONFIG.temp.interval)

        self.enabled = CONFIG.temp.enabled

    async def update(self) -> None:
        """Update output with current date/time in chosen format."""
        if not self.enabled:
            return

        temp = round(float(psutil.sensors_temperatures()[CONFIG.temp.device][0].current))

        icon = next(icon for threshold, icon in self.thresholds.items() if temp >= threshold)
        self.output = f"{icon} {temp}°C"

        if self.updater is not None:
            self.updater.update_event.set()
