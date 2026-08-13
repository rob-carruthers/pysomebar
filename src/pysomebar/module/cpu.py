"""CPU usage module for pysomebar."""

from types import MappingProxyType
from typing import TYPE_CHECKING

import psutil

from pysomebar.config import CONFIG

from .module import Module

if TYPE_CHECKING:
    from pysomebar.util import ColoriserProtocol


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

    def __init__(self, coloriser: ColoriserProtocol | None) -> None:  # noqa: D107
        super().__init__(coloriser=coloriser, name=self.name, interval=CONFIG.cpu.interval)

    async def update(self) -> None:
        """Update output with current CPU usage."""
        cpu = psutil.cpu_percent()
        cpu = min(cpu, 99.9)

        self.output = " " + f"{cpu}%".rjust(5)

        if self.coloriser is not None:
            color = next(color for thresh, color in self.colors.items() if cpu >= thresh)
            self.output = self.coloriser(self.output, fg=color)

        await self.request_redraw()
