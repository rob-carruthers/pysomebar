"""Modules for pysomebar."""

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pysomebar.updater import Updater


class Module(ABC):
    """Abstract base class for modules."""

    def __init__(self, interval: int) -> None:  # noqa: D107
        self.updater: Updater | None = None
        self.interval = interval
        self.do_initial_update = True
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
