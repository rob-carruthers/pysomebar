"""Main entry point for pysomebar."""

import asyncio

from pysomebar.config import CONFIG

from .module import (
    BatteryModule,
    BrightnessModule,
    DateModule,
    PortageModule,
    PulseModule,
    TempModule,
)
from .updater import SomebarUpdater


async def main_loop() -> None:
    """Start main async loop."""
    match CONFIG.bar_type:
        case "somebar":
            updater = SomebarUpdater()

    await updater.add_module(PulseModule())
    await updater.add_module(BrightnessModule())
    await updater.add_module(TempModule())
    await updater.add_module(BatteryModule())
    await updater.add_module(PortageModule())
    await updater.add_module(DateModule())
    await updater.initial_update()
    await updater.loop()


def main() -> None:  # noqa: D103
    asyncio.run(main_loop())
