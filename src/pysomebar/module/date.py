"""Date module for pysomebar."""

import datetime

from pysomebar.config import CONFIG

from .module import Module


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
