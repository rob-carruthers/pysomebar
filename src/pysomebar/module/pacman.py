"""Pacman updates module for pysomebar."""

import asyncio
from typing import TYPE_CHECKING

from pysomebar.config import CONFIG

from .module import NeedsInternetModule

if TYPE_CHECKING:
    from pysomebar.util import ColoriserProtocol

RESTART_PACKAGES = ("linux", "systemd")


class PacmanModule(NeedsInternetModule):
    """Module for checking Arch package update status."""

    name = "pacman"

    def __init__(self, coloriser: ColoriserProtocol | None) -> None:  # noqa: D107
        super().__init__(coloriser=coloriser, name=self.name, interval=CONFIG.pacman.interval)

        self.refresh_signal = 1
        self.raw_output = self.output

    async def update(self) -> None:  # noqa: D102
        for _ in range(self.connect_retries):
            if await self.is_internet_available():
                await self.make_output()
                return

            await asyncio.sleep(self.retry_interval)

            self.output = "No network!"
            self.raw_output = "No network!"

    async def get_updates(self) -> tuple[int, bool] | None:
        """Return update count and restart status, or None if checkupdates couldn't run/sync.

        Returns
        -------
        int
            Update count
        bool
            Whether a restart is required

        """
        no_updates = 2
        try:
            proc = await asyncio.create_subprocess_exec(
                "/usr/bin/checkupdates",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return None
        except OSError:
            return None

        if proc.returncode == no_updates:
            return 0, False
        if proc.returncode != 0:
            return None

        updates = [line for line in stdout.decode().split("\n") if line]
        restart_required = any(line.split(" ", 1)[0] in RESTART_PACKAGES for line in updates)
        return len(updates), restart_required

    async def make_output(self) -> None:
        """Set 'spinner', get `n_updates` and update status."""
        self.output = "Updating..."
        await self.request_redraw()

        result = await self.get_updates()

        if result is None:
            self.output = "No network!"
        elif result[0] > 0:
            self.output = str(result[0]) + (" update" if result[0] == 1 else " updates")
            self.output += " (restart)" if result[1] else ""
            self.raw_output = self.output
            if self.coloriser is not None:
                self.output = self.coloriser(
                    self.output,
                    fg=CONFIG.pacman.available_updates_color,
                )
        else:
            self.output = "No updates"
            self.raw_output = self.output

        await self.request_redraw()
