"""Main entry point for pysomebar."""

import asyncio
import os
import random
from pathlib import Path

import aiofiles
from .module import DateModule, Module

XDG_RUNTIME_DIR = os.environ["XDG_RUNTIME_DIR"]
SOMEBAR = Path(XDG_RUNTIME_DIR) / "somebar-0"
RETRIES = 10


class SomebarUpdater:
    def __init__(self, separator: str = " | "):
        self.separator = separator
        self._modules: list[Module] = []
        self.modules: list[Module] = []
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

        async with aiofiles.open(SOMEBAR, "w") as f:
            status = f"status {joined_output}\n"
            await f.write(status)

        self.update_event.clear()

    async def initial_update(self) -> None:
        """Initialise state/output for all held modules."""
        if len(self._modules) < 1:
            return

        for module in self._modules:
            await module.update()

        await self.write_output()

    async def loop(self) -> None:
        """Continuously wait for updates/interval timeouts and write to named pipe."""
        if len(self._modules) < 1:
            return

        while True:
            await self.update_event.wait()
            await asyncio.sleep(0.02)
            await self.write_output()


async def main_loop() -> None:
    """Start main async loop."""
    updater = SomebarUpdater()
    await updater.add_module(DateModule(1))
    await updater.add_module(RandomModule(1.5))
    await updater.initial_update()
    await updater.loop()


def main() -> None:
    for _ in range(RETRIES):
        if SOMEBAR.exists():
            break
    else:
        raise FileNotFoundError

    asyncio.run(main_loop())
