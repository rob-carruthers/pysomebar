"""Updater for picostatus."""

import asyncio
import datetime
import json
from typing import TYPE_CHECKING, Literal

import serial_asyncio

from pysomebar.module import Module, MPDModule, PacmanModule, PortageModule, PulseModule, YNABModule

if TYPE_CHECKING:
    from pysomebar.module.mpd import MPDPlayerState

PicoStatusInputDataType = Literal["time", "mpd", "updates", "pulse", "ynab"]


class PicoStatusUpdater:
    """Updater for `picostatus`.

    `picostatus` is a small module for a Raspberry Pi Pico (1/2) + SSD1305 display. It receives
    string JSON data via USB CDC and displays status information.

    This information is fed from `pysomebar` modules.
    """

    def __init__(
        self,
        modules: dict[str, Module],
        port: str = "/dev/ttyACM1",
        baud: int = 115200,
        interval_secs: float = 0.25,
        debounce_secs: float = 0.05,
    ) -> None:
        """Initialise USB CDC writer."""
        self.modules = modules
        self.port = port
        self.baud = baud
        self.interval_secs = interval_secs
        self.debounce_secs = debounce_secs
        self.reader: asyncio.StreamReader
        self.writer: asyncio.StreamWriter
        self.update_event = asyncio.Event()
        self.last_write = 0.0

    async def connect(self) -> None:
        """Connect to chosen USB CDC device."""
        self.reader, self.writer = await serial_asyncio.open_serial_connection(
            url=self.port,
            baudrate=self.baud,
        )

    def get_mpd_data(self) -> tuple[str, MPDPlayerState, int, int]:
        """Retrieve latest MPD data from running MPDModule."""
        mpd_module = self.modules.get("mpd")
        if not isinstance(mpd_module, MPDModule) or mpd_module.status is None:
            return "mpd not loaded", "stop", 0, 100

        status = mpd_module.status
        if status.state == "stop":
            return "Stopped", "stop", status.pos, status.dur

        if status.artist == "Unknown":
            now_playing = status.title
        else:
            now_playing = status.artist + " - " + status.title
        return now_playing, status.state, status.pos, status.dur

    def get_pacman_data(self) -> str | None:
        """Retrieve latest pacman data from running PacmanModule."""
        pacman_module = self.modules.get("pacman")
        if not isinstance(pacman_module, PacmanModule):
            return None

        return pacman_module.raw_output

    def get_portage_data(self) -> str | None:
        """Retrieve latest portage data from running portageModule."""
        portage_module = self.modules.get("portage")
        if not isinstance(portage_module, PortageModule):
            return None

        return portage_module.raw_output

    def get_ynab_data(self) -> str | None:
        """Retrieve latest YNAB data from running YNABModule."""
        ynab_module = self.modules.get("ynab")
        if not isinstance(ynab_module, YNABModule):
            return None

        return ynab_module.raw_output

    def get_pulse_data(self) -> tuple[str, bool]:
        """Retrieve latest PulseAudio data from running PulseModule."""
        pulse_module = self.modules.get("pulse")
        if not isinstance(pulse_module, PulseModule):
            return "No volume!", False

        muted = "M " if pulse_module.current_muted else "  "
        vol = str(pulse_module.current_volume).rjust(3)
        return f"{muted}{vol}%", pulse_module.is_headset

    def get_current_time(self, fmt: str = "%H:%M:%S") -> str:
        """Get the current time as string."""
        now = datetime.datetime.now(tz=datetime.UTC).astimezone()
        return now.strftime(fmt)

    def format_status(self) -> dict[PicoStatusInputDataType, dict[str, str | int]]:
        """Create the status data as dict from modules."""
        mpd_now_playing, state, pos, dur = self.get_mpd_data()
        pacman_updates = self.get_pacman_data()
        portage_updates = self.get_portage_data()
        ynab_data = self.get_ynab_data() or "N/A"
        current_volume, is_headset = self.get_pulse_data()
        now = self.get_current_time()

        if pacman_updates:
            updates = pacman_updates
        elif portage_updates:
            updates = portage_updates
        else:
            updates = "No updates"

        return {
            "time": {"text": now},
            "mpd": {"text": mpd_now_playing, "state": state, "dur": dur, "pos": pos},
            "updates": {"text": updates},
            "pulse": {"text": current_volume, "is_headset": is_headset},
            "ynab": {"text": ynab_data},
        }

    async def main_loop(self) -> None:
        """Continuously wait for an update event or the next tick boundary, then write.

        Attempt to synchronise ticks to wall clock using interval_secs.
        """
        while True:
            line = json.dumps(self.format_status())
            self.writer.write((line + "\n").encode())
            await self.writer.drain()
            self.last_write = asyncio.get_running_loop().time()

            now = datetime.datetime.now(tz=datetime.UTC).timestamp()
            next_tick = (now // self.interval_secs + 1) * self.interval_secs
            timeout = next_tick - now

            try:
                await asyncio.wait_for(self.update_event.wait(), timeout=timeout)
                self.update_event.clear()
            except TimeoutError:
                continue

            # If the event fired early on update_event, debounce before continuing
            elapsed = asyncio.get_running_loop().time() - self.last_write
            if elapsed < self.debounce_secs:
                await asyncio.sleep(self.debounce_secs - elapsed)

    async def run(self) -> None:
        """Run the main loop."""
        await self.connect()
        try:
            await self.main_loop()
        finally:
            self.writer.close()
