"""Main entry point for pysomebar."""

import asyncio
import os
import time
from pathlib import Path

import aiofiles

from .module import BatteryModule, BrightnessModule, DateModule, Module, PulseModule, TempModule

XDG_RUNTIME_DIR = os.environ["XDG_RUNTIME_DIR"]
SOMEBAR = Path(XDG_RUNTIME_DIR) / "somebar-0"
RETRIES = 10


class SomebarUpdater:
    """Orchestrator for updater.

    Contains Modules and handles writing to output.
    """

    def __init__(self, separator: str = " | ") -> None:  # noqa: D107
        self.separator = separator
        self._modules: list[Module] = []
        self.output: str = ""
        self.last_output: str = ""
        self.update_event = asyncio.Event()
        self.tasks: set[asyncio.Task] = set()

    async def add_module(self, module: Module) -> None:
        """Add a module to this updater."""
        if not module.enabled:
            return

        module.updater = self
        self.tasks.add(asyncio.create_task(module.loop()))
        self._modules.append(module)

    async def write_output(self) -> None:
        """Write output to somebar's named pipe."""
        joined_output = " | ".join(module.output for module in self._modules)

        if joined_output != self.last_output:
            async with aiofiles.open(SOMEBAR, "w") as f:
                status = f"status {joined_output}\n"
                await f.write(status)

            self.last_output = joined_output

        self.update_event.clear()

    async def initial_update(self) -> None:
        """Initialise state/output for all held modules."""
        if len(self._modules) < 1:
            return

        for module in self._modules:
            if not module.do_initial_update:
                continue
            await module.update()

        await self.write_output()

    async def loop(self) -> None:
        """Continuously wait for updates/interval timeouts and write to named pipe."""
        if len(self._modules) < 1:
            return

        while True:
            await self.update_event.wait()
            await asyncio.sleep(0)
            await self.write_output()


async def main_loop() -> None:
    """Start main async loop."""
    updater = SomebarUpdater()
    await updater.add_module(PulseModule())
    await updater.add_module(BrightnessModule())
    await updater.add_module(TempModule())
    await updater.add_module(BatteryModule())
    await updater.add_module(DateModule())
    await updater.initial_update()
    await updater.loop()


def main() -> None:  # noqa: D103
    for _ in range(RETRIES):
        if SOMEBAR.exists():
            break
        time.sleep(0.5)
    else:
        raise FileNotFoundError

    asyncio.run(main_loop())
