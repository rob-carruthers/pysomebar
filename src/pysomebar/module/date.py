"""Date module for pysomebar."""

import datetime

from pysomebar.config import CONFIG

from .module import Module


class DateModule(Module):
    """Module for printing date/time."""

    name = "date"

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.date.interval)

    async def update(self) -> None:
        """Update output with current date/time in chosen format."""
        now = datetime.datetime.now().astimezone().strftime(CONFIG.date.format)
        self.output = now
        if self.updater is not None:
            self.updater.update_event.set()
