"""CPU usage module for pysomebar."""

from types import MappingProxyType

import psutil

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

from .module import Module


class CPUModule(Module):
    """Module for showing current CPU usage."""

    name = "cpu"

    colors = MappingProxyType(
        {
            CONFIG.cpu.red_threshold: "red_d",
            CONFIG.cpu.yellow_threshold: "yellow_d",
            -1: CONFIG.base_color,
        },
    )

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.cpu.interval)

    async def update(self) -> None:
        """Update output with current CPU usage."""
        cpu = psutil.cpu_percent()

        self.output = f" {cpu}%"

        if CONFIG.bar_type == "dwlb":
            color = next(color for thresh, color in self.colors.items() if cpu >= thresh)
            self.output = make_dwlb_colored_text(self.output, fg=color)

        await self.request_redraw()
