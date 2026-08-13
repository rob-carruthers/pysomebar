"""Temp module for pysomebar."""

from types import MappingProxyType
from typing import TYPE_CHECKING

import psutil

from pysomebar.config import CONFIG

from .module import Module

if TYPE_CHECKING:
    from pysomebar.util import ColoriserProtocol


def convert_time(seconds: int) -> str:
    """Convert seconds to a formatting string of {hours}:{minutes}:{seconds}."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"


class TempModule(Module):
    """Module for showing temps."""

    name = "temp"

    icons = MappingProxyType({75: "", 60: "", 50: "", -274: ""})
    colors = MappingProxyType(
        {
            CONFIG.temp.red_threshold: "red_d",
            CONFIG.temp.yellow_threshold: "yellow_d",
            -274: "green_d",
        },
    )

    def __init__(self, coloriser: ColoriserProtocol | None) -> None:  # noqa: D107
        super().__init__(coloriser=coloriser, name=self.name, interval=CONFIG.temp.interval)

    async def update(self) -> None:
        """Update output with current date/time in chosen format."""
        temp = round(float(psutil.sensors_temperatures()[CONFIG.temp.device][0].current))

        icon = next(icon for thresh, icon in self.icons.items() if temp >= thresh)
        self.output = f"{icon} {temp}°C"

        if self.coloriser is not None:
            color = next(color for thresh, color in self.colors.items() if temp >= thresh)
            self.output = self.coloriser(self.output, fg=color)

        await self.request_redraw()
