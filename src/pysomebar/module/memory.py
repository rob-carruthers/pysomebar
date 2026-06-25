"""Used / available memory module for pysomebar."""

from typing import TYPE_CHECKING

import psutil

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

from .module import Module

if TYPE_CHECKING:
    from psutil._ntuples import svmem


def format_bytes(b: float, base: int = 1024) -> str:
    """Format n bytes output to B/K/M/G.

    If G, then round to 1dp, otherwise round to nearest integer.
    """
    round_n = None
    if b < base:
        return f"{round(b, round_n)}B"
    if b < (base**2):
        return f"{round(b / base, round_n)}K"
    if b < (base**3):
        return f"{round(b / base**2, round_n)}M"

    round_n = 1
    return f"{round(b / base**3, round_n)}G"


class MemoryModule(Module):
    """Module for showing current used memory."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(CONFIG.memory.interval)

        self.enabled = CONFIG.memory.enabled

    async def update(self) -> None:
        """Update output with current battery status."""
        if not self.enabled:
            return

        mem: svmem = psutil.virtual_memory()

        # Matching htop's calculation of 'used' mem
        used_gb = format_bytes(mem.total - mem.free - mem.cached)
        available_gb = format_bytes(mem.total)

        self.output = f"{used_gb} / {available_gb}"

        if CONFIG.bar_type == "dwlb":
            self.output = make_dwlb_colored_text(self.output, fg=CONFIG.base_color)

        if self.updater is not None:
            self.updater.update_event.set()
