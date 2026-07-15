"""Date module for pysomebar."""

import datetime

from pysomebar.config import CONFIG

from .module import Module


class DateModule(Module):
    """Module for printing date/time."""

    name = "date"

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.date.interval)

        # Set static base_interval - self.interval may change to sync to 0 seconds
        self.base_interval = CONFIG.date.interval

    async def update(self) -> None:
        """Update output with current date/time in chosen format."""
        now = datetime.datetime.now().astimezone()
        self.output = now.strftime(CONFIG.date.format)

        # Sync refresh to zeroth second, regardless of our chosen interval
        seconds_into_min = now.timestamp() % 60
        remaining_in_min = 60 - seconds_into_min
        next_tick = self.base_interval - (seconds_into_min % self.base_interval)

        # Update self.interval as we might need a shorter interval to hit '0' of minute
        self.interval = min(next_tick, remaining_in_min)

        await self.request_redraw()
