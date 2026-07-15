"""Used / available memory module for pysomebar."""

from types import MappingProxyType
from typing import TYPE_CHECKING

import psutil

from pysomebar.config import CONFIG
from pysomebar.util import format_bytes, make_dwlb_colored_text

from .module import Module

if TYPE_CHECKING:
    from psutil._ntuples import svmem


class MemoryModule(Module):
    """Module for showing current used memory."""

    name = "memory"
    colors = MappingProxyType(
        {
            CONFIG.memory.red_threshold: "red_d",
            CONFIG.memory.yellow_threshold: "yellow_d",
            -1: CONFIG.base_color,
        },
    )

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.memory.interval)

    async def update(self) -> None:
        """Update output with current battery status."""
        mem: svmem = psutil.virtual_memory()

        # Matching htop's calculation of 'used' mem
        used = mem.total - mem.free - mem.cached
        used_gb = format_bytes(used)
        available_gb = format_bytes(mem.total)

        used_percent = 100 * used / mem.total

        self.output = f" {used_gb} / {available_gb}"

        if CONFIG.bar_type == "dwlb":
            color = next(color for thresh, color in self.colors.items() if used_percent >= thresh)
            self.output = make_dwlb_colored_text(self.output, fg=color)

        await self.request_redraw()
