"""Modules for pysomebar."""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pysomebar import SomebarUpdater


class Module(ABC):
    """Abstract base class for modules."""

    def __init__(self, interval: int) -> None:  # noqa: D107
        self.updater: SomebarUpdater | None = None
        self.interval = interval
        self.output: str = ""
        self.enabled: bool = False

    @abstractmethod
    async def update(self) -> None:
        """Abstract method for updating asynchronously."""
        ...

    async def loop(self) -> None:
        """Loop over interval/async updates."""
        if not self.enabled:
            return

        while True:
            try:
                await asyncio.wait_for(self.update(), timeout=self.interval)
            except asyncio.TimeoutError:  # noqa: UP041
                continue
            await asyncio.sleep(self.interval)


class RandomModule(Module):
    def __init__(self, interval: int):
        super().__init__(interval)

    async def update(self) -> None:
        if not self.enabled:
            return

        self.output = str(random.randint(0, 10))
        if self.updater is not None:
            self.updater.update_event.set()
