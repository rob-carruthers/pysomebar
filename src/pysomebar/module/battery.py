"""Battery module for pysomebar."""

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


class BatteryModule(Module):
    """Module for showing battery status and calculating remaining time."""

    name = "battery"
    charging_icons = MappingProxyType(
        {
            0: "󰢟",
            10: "󰢜",
            20: "󰂆",
            30: "󰂇",
            40: "󰂈",
            50: "󰢝",
            60: "󰂉",
            70: "󰢞",
            80: "󰂊",
            90: "󰂋",
            100: "󰂅",
        },
    )
    discharging_icons = MappingProxyType(
        {
            0: "󰂎",
            10: "󰁺",
            20: "󰁻",
            30: "󰁼",
            40: "󰁽",
            50: "󰁾",
            60: "󰁿",
            70: "󰂀",
            80: "󰂁",
            90: "󰂂",
            100: "󰁹",
        },
    )
    colors = MappingProxyType(
        {
            CONFIG.battery.green_threshold: "green_d",
            CONFIG.battery.yellow_threshold: "yellow_d",
            -1: "red_d",
        },
    )

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.battery.interval)

    def get_icon(self, percent: float, *, is_charging: bool = False) -> str:
        """Retrieve an appropriate icon from self.(dis)charging_icons."""
        rounded = int((percent // 10) * 10)
        if is_charging:
            return self.charging_icons.get(rounded, "󰂅")

        return self.discharging_icons.get(rounded, "󰁹")

    def make_output(self, percent: float, remaining_s: int, *, is_charging: bool) -> str:
        """Make the final output for status."""
        icon = self.get_icon(percent, is_charging=is_charging)
        formatted_time = convert_time(remaining_s)

        if is_charging:
            return f"{icon} {int(percent)}%, charging"

        if remaining_s in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED):
            return f"{icon} {int(percent)}%"

        return f"{icon} {int(percent)}%, {formatted_time} remaining"

    async def update(self) -> None:
        """Update output with current battery status."""
        battery = psutil.sensors_battery()
        is_charging = battery.power_plugged is True
        self.output = self.make_output(battery.percent, battery.secsleft, is_charging=is_charging)

        if CONFIG.bar_type == "dwlb":
            rounded = int((battery.percent // 10) * 10)
            color = next(color for thresh, color in self.colors.items() if rounded >= thresh)
            self.output = make_dwlb_colored_text(self.output, fg=color)

        await self.request_redraw()
