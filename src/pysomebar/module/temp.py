"""Temp module for pysomebar."""

from types import MappingProxyType

import psutil

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

from .module import Module


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

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.temp.interval)

    async def update(self) -> None:
        """Update output with current date/time in chosen format."""
        temp = round(float(psutil.sensors_temperatures()[CONFIG.temp.device][0].current))

        icon = next(icon for thresh, icon in self.icons.items() if temp >= thresh)
        self.output = f"{icon} {temp}°C"

        if CONFIG.bar_type == "dwlb":
            color = next(color for thresh, color in self.colors.items() if temp >= thresh)
            self.output = make_dwlb_colored_text(self.output, fg=color)

        if self.updater is not None:
            self.updater.update_event.set()
