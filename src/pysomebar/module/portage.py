"""Portage updates module for pysomebar."""

import asyncio
import re
from typing import TYPE_CHECKING

from asyncinotify import Mask

from pysomebar.config import CONFIG

from .module import Module

if TYPE_CHECKING:
    from pysomebar.util import ColoriserProtocol


class PortageModule(Module):
    """Module for printing date/time."""

    name = "portage"

    def __init__(  # noqa: D107
        self,
        coloriser: ColoriserProtocol | None,
        spinner: str = "Syncing portage...",
    ) -> None:
        super().__init__(coloriser=coloriser, name=self.name, interval=CONFIG.portage.interval)

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
            await self.request_redraw()

            n_updates = await self.get_n_updates()

        if n_updates == 0:
            self.output = "No updates"
        elif n_updates == 1:
            self.output = "1 update"
        else:
            self.output = f"{n_updates} updates"

        if self.coloriser is not None and n_updates > 0:
            self.output = self.coloriser(self.output, fg=CONFIG.portage.available_updates_color)

        await self.request_redraw()

    async def loop(self) -> None:
        """Update output with current n updates.."""
        await self.make_output()

        async for _ in self.watch_files(
            CONFIG.portage.watch_file,
            mask=Mask.MODIFY | Mask.MOVED_TO,
        ):
            await self.make_output()
