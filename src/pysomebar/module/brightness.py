"""Brightness module for pysomebar."""

from pathlib import Path

import aiofiles
from asyncinotify import Mask

from pysomebar.config import CONFIG

from .module import Module


class BrightnessModule(Module):
    """Module for monitoring brightness via /sys/class/backlight/."""

    name = "brightness"

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.brightness.interval)

        self.do_initial_update = False

    async def update(self) -> None:
        """Passthrough as we handle everything in loop()."""

    async def get_brightness(self) -> int | None:
        """Retrieve brightness % from /sys/class/backlight/."""
        if CONFIG.brightness.device is None:
            return None

        backlight_dir = Path("/sys/class/backlight") / CONFIG.brightness.device
        async with aiofiles.open(backlight_dir / "brightness") as f:
            brightness = int(await f.read())

        async with aiofiles.open(backlight_dir / "max_brightness") as f:
            max_brightness = int(await f.read())

        return round(100 * brightness / max_brightness)

    async def make_output(self, brightness_percent: int | None) -> None:
        """Make output from brightness percent."""
        self.output = f"󰍹 {brightness_percent}%"

        if self.updater is not None:
            self.updater.update_event.set()

    async def loop(self) -> None:
        """Update output with current date/time in chosen format."""
        if CONFIG.brightness.device is None:
            return

        brightness_file = Path("/sys/class/backlight") / CONFIG.brightness.device / "brightness"

        if not brightness_file.exists():
            raise FileNotFoundError

        brightness_percent = await self.get_brightness()
        await self.make_output(brightness_percent)

        # Watch for MODIFY events, i.e. when the brightness has actually changed
        # (brightnessctl, for example, writes directly to this file)
        async for _ in self.watch_files(brightness_file, mask=Mask.MODIFY):
            brightness_percent = await self.get_brightness()

            await self.make_output(brightness_percent)
