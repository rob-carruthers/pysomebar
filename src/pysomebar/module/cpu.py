"""CPU usage module for pysomebar."""

import psutil

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

from .module import Module


class CPUModule(Module):
    """Module for showing current CPU usage."""

    name = "cpu"

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.cpu.interval)

    async def update(self) -> None:
        """Update output with current CPU usage."""
        cpu = psutil.cpu_percent()

        self.output = f"{cpu}%"

        if CONFIG.bar_type == "dwlb":
            self.output = make_dwlb_colored_text(self.output, fg=CONFIG.base_color)

        await self.request_redraw()
