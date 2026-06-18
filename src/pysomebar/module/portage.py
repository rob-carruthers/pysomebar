"""Portage updates module for pysomebar."""

import asyncio
import re

from asyncinotify import Mask

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

from .module import Module


class PortageModule(Module):
    """Module for printing date/time."""

    def __init__(self, spinner: str = "Syncing portage...") -> None:  # noqa: D107
        super().__init__(CONFIG.portage.interval)

        self.enabled = CONFIG.portage.enabled
        self.do_initial_update = False
        self.spinner = spinner
        self._lock = asyncio.Lock()

    async def update(self) -> None:
        """Passthrough as we handle everything in loop()."""

    async def get_n_updates(self) -> int:
        """Get the number of portage updates available by running `emerge -NupDq world`."""
        proc = await asyncio.create_subprocess_exec(
            "/usr/bin/emerge",
            "-NupDq",
            "world",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode().split("\n")
        updates = [line for line in lines if re.match(r"\[.*\]", line)]
        return len(updates)

    async def make_output(self) -> None:
        """Set 'spinner', get `n_updates` and update status."""
        async with self._lock:
            self.output = self.spinner
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

    async def loop(self) -> None:
        """Update output with current n updates.."""
        if not self.enabled:
            return

        await self.make_output()

        async for _ in self.watch_files(
            CONFIG.portage.watch_file,
            mask=Mask.MODIFY | Mask.MOVED_TO,
        ):
            await self.make_output()
