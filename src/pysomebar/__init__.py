"""Main entry point for pysomebar."""

import asyncio
import contextlib

from pysomebar.config import CONFIG

from .module import (
    BatteryModule,
    BrightnessModule,
    DateModule,
    PortageModule,
    PulseModule,
    TempModule,
)
from .updater import DwlbUpdater, SomebarUpdater


async def main_loop() -> None:
    """Start main async loop."""
    match CONFIG.bar_type:
        case "somebar":
            updater = SomebarUpdater()
        case "dwlb":
            updater = DwlbUpdater()

    await updater.add_module(PulseModule())
    await updater.add_module(BrightnessModule())
    await updater.add_module(TempModule())
    await updater.add_module(BatteryModule())
    await updater.add_module(PortageModule())
    await updater.add_module(DateModule())
    await updater.initial_update()
    await updater.loop()


def main() -> None:  # noqa: D103
    with contextlib.suppress(KeyboardInterrupt, BrokenPipeError):
        asyncio.run(main_loop())
