"""Main entry point for pysomebar."""

import asyncio
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

if TYPE_CHECKING:
    from .module import Module


class Updater(ABC):
    """Orchestrator for updater.

    Contains Modules and handles writing to output.

    Should be subclassed for a specific implementation (e.g. `somebar`, `dwlb`...)
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

    @abstractmethod
    async def write_output(self) -> None:
        """Write output to bar."""

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


class SomebarUpdater(Updater):
    """Updater for `somebar`."""

    def __init__(self, separator: str = " | ") -> None:  # noqa: D107
        super().__init__(separator)
        xdg_runtime_dir = os.environ["XDG_RUNTIME_DIR"]
        self.somebar = Path(xdg_runtime_dir) / "somebar-0"

        retries = 10
        for _ in range(retries):
            if self.somebar.exists():
                break
            time.sleep(0.5)
        else:
            raise FileNotFoundError

    async def write_output(self) -> None:
        """Write output to somebar's named pipe."""
        joined_output = " | ".join(module.output for module in self._modules)

        if joined_output != self.last_output:
            async with aiofiles.open(self.somebar, "w") as f:
                status = f"status {joined_output}\n"
                await f.write(status)

            self.last_output = joined_output

        self.update_event.clear()
