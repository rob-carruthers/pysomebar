"""Battery module for pysomebar."""

from types import MappingProxyType

import psutil

from pysomebar.config import CONFIG

from .module import Module


def convert_time(seconds: int) -> str:
    """Convert seconds to a formatting string of {hours}:{minutes}:{seconds}."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"


class BatteryModule(Module):
    """Module for showing battery status and calculating remaining time."""

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

    def __init__(self) -> None:  # noqa: D107
        super().__init__(CONFIG.battery.interval)

        self.enabled = CONFIG.battery.enabled

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
        if not self.enabled:
            return

        battery = psutil.sensors_battery()
        is_charging = battery.power_plugged is True
        self.output = self.make_output(battery.percent, battery.secsleft, is_charging=is_charging)

        if self.updater is not None:
            self.updater.update_event.set()
