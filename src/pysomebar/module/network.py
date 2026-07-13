"""Network usage module for pysomebar."""

import psutil

from pysomebar.config import CONFIG
from pysomebar.util import format_bytes, make_dwlb_colored_text

from .module import Module


class NetworkModule(Module):
    """Module for showing current network usage."""

    name = "network"
    recv_icon = ""
    sent_icon = ""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.network.interval)

        self.enabled = CONFIG.network.enabled
        self.device = CONFIG.network.device
        self.padding = CONFIG.network.padding
        self.gate = CONFIG.network.gate
        self.recv, self.sent = self.get_counts()

    def get_counts(self) -> tuple[int, int]:
        """Get current counts of received and sent bytes.

        If self.device is None, return totals for all interfaces. Else, just self.device.
        """
        if self.device is None:
            counts = psutil.net_io_counters()
            recv = counts.bytes_recv
            sent = counts.bytes_sent
        else:
            counts = psutil.net_io_counters(pernic=True)
            try:
                recv = counts[self.device].bytes_recv
                sent = counts[self.device].bytes_sent
            except KeyError as e:
                msg = f"Device `{self.device}` not found."
                raise ValueError(msg) from e

        return recv, sent

    def get_rate_formatted(self, new_count: int, prev_count: int) -> str:
        """Calculate rate per second and format to B/K/M/G."""
        diff = max(new_count - prev_count, 0)

        rate = diff / self.interval

        if rate < self.gate:
            rate = 0

        return (format_bytes(rate) + "/s").rjust(self.padding)

    async def update(self) -> None:
        """Update output with current battery status."""
        if not self.enabled:
            return

        # Output gracefully if configured network device suddenly isn't available
        try:
            new_recv, new_sent = self.get_counts()
        except ValueError:
            self.output = f"{self.recv_icon} ?/s {self.sent_icon} ?/s"
            return

        rate_recv = self.get_rate_formatted(new_recv, self.recv)
        rate_sent = self.get_rate_formatted(new_sent, self.sent)

        self.output = f"{self.recv_icon} {rate_recv} {self.sent_icon} {rate_sent}"
        self.recv, self.sent = new_recv, new_sent

        if CONFIG.bar_type == "dwlb":
            self.output = make_dwlb_colored_text(self.output, fg=CONFIG.base_color)

        if self.updater is not None:
            self.updater.update_event.set()
