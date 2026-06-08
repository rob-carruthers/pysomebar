"""Modules for pysomebar."""

import asyncio
import datetime
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .config import CONFIG

if TYPE_CHECKING:
    from . import SomebarUpdater


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
        if not self.enabled:
            return

        while True:
            try:
                await asyncio.wait_for(self.update(), timeout=self.interval)
            except asyncio.TimeoutError:  # noqa: UP041
                continue
            await asyncio.sleep(self.interval)


class DateModule(Module):
    """Module for printing date/time."""

    def __init__(self, interval: int) -> None:  # noqa: D107
        super().__init__(interval)

        self.enabled = CONFIG.date.enabled

    async def update(self) -> None:
        """Update output with current date/time in chosen format."""
        if not self.enabled:
            return

        now = datetime.datetime.now().astimezone().strftime(CONFIG.date.format)
        self.output = now
        if self.updater is not None:
            self.updater.update_event.set()
