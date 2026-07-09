"""Pacman updates module for pysomebar."""

import asyncio

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

from .module import Module


class PacmanModule(Module):
    """Module for printing date/time."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(CONFIG.pacman.interval)

        self.enabled = CONFIG.pacman.enabled

    async def update(self) -> None:  # noqa: D102
        if not self.enabled:
            return

        await self.make_output()

    async def get_n_updates(self) -> int:
        """Get the number of portage updates available by running `emerge -NupDq world`."""
        proc = await asyncio.create_subprocess_exec(
            "/usr/bin/checkupdates",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        if not stdout:
            return 0

        lines = [line for line in stdout.decode().split("\n") if line]

        return len(lines)

    async def make_output(self) -> None:
        """Set 'spinner', get `n_updates` and update status."""
        if self.updater is not None:
            self.updater.update_event.set()

        n_updates = await self.get_n_updates()

        self.output = f"Updates: {n_updates}" if n_updates > 0 else "No updates"

        if CONFIG.bar_type == "dwlb" and n_updates > 0:
            self.output = make_dwlb_colored_text(
                self.output,
                fg=CONFIG.portage.available_updates_color,
            )

        if self.updater is not None:
            self.updater.update_event.set()
