"""Portage updates module for pysomebar."""

import asyncio
import re
import subprocess

from asyncinotify import Mask

from pysomebar.config import CONFIG

from .module import Module


class PortageModule(Module):
    """Module for printing date/time."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(CONFIG.portage.interval)

        self.enabled = CONFIG.portage.enabled
        self.do_initial_update = False
        self._lock = asyncio.Lock()

    async def update(self) -> None:
        """Passthrough as we handle everything in loop()."""

    def get_n_updates(self) -> int:
        """Get the number of portage updates available by running `emerge -NupDq world`."""
        result = subprocess.run(
            ["/usr/bin/emerge", "-NupDq", "world"],
            check=False,
            capture_output=True,
        )
        stdout = result.stdout.decode().split("\n")

        updates = [line for line in stdout if re.match(r"\[.*\]", line)]

        return len(updates)

    async def make_output(self, n_updates: int) -> None:
        """Make output from n_updates."""
        self.output = f"Updates: {n_updates}"

        if self.updater is not None:
            self.updater.update_event.set()

    async def loop(self) -> None:
        """Update output with current n updates.."""
        if not self.enabled:
            return

        async with self._lock:
            n_updates = await asyncio.to_thread(self.get_n_updates)
        await self.make_output(n_updates)

        async for _ in self.watch_files(
            CONFIG.portage.watch_file,
            mask=Mask.MODIFY | Mask.MOVED_TO,
        ):
            async with self._lock:
                n_updates = await asyncio.to_thread(self.get_n_updates)
            await self.make_output(n_updates)
