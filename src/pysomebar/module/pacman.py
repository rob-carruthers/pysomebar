"""Pacman updates module for pysomebar."""

import asyncio

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

from .module import NeedsInternetModule


class PacmanModule(NeedsInternetModule):
    """Module for printing date/time."""

    name = "pacman"

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.pacman.interval)

        self.refresh_signal = 1

    async def update(self) -> None:  # noqa: D102
        await self.make_output()

    async def get_n_updates(self) -> int | None:
        """Return update count, or None if checkupdates couldn't run/sync."""
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
            return 0
        if proc.returncode != 0:
            return None

        return len([line for line in stdout.decode().split("\n") if line])

    async def make_output(self) -> None:
        """Set 'spinner', get `n_updates` and update status."""
        self.output = "Updating..."
        await self.request_redraw()

        n_updates = await self.get_n_updates()

        if n_updates is None:
            self.output = "No network!"
        elif n_updates > 0:
            self.output = f"Updates: {n_updates}"
            if CONFIG.bar_type == "dwlb":
                self.output = make_dwlb_colored_text(
                    self.output,
                    fg=CONFIG.pacman.available_updates_color,
                )
        else:
            self.output = "No updates"

        await self.request_redraw()
