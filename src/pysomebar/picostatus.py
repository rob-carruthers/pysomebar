"""Updater for picostatus."""

import asyncio
import datetime
import json
from typing import TYPE_CHECKING, Literal

import serial_asyncio

from pysomebar.module import Module, MPDModule, PacmanModule, PulseModule

if TYPE_CHECKING:
    from pysomebar.module.mpd import MPDPlayerState

PicoStatusInputDataType = Literal["time", "mpd", "pacman", "pulse"]


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
        interval_secs: float = 0.5,
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

        now_playing = status.artist + " - " + status.title
        return now_playing, status.state, status.pos, status.dur

    def get_pacman_data(self) -> str:
        """Retrieve latest pacman data from running PacmanModule."""
        pacman_module = self.modules.get("pacman")
        if not isinstance(pacman_module, PacmanModule):
            return "No network!"

        return pacman_module.raw_output

    def get_pulse_data(self) -> tuple[str, bool]:
        """Retrieve latest PulseAudio data from running PulseModule."""
        pulse_module = self.modules.get("pulse")
        if not isinstance(pulse_module, PulseModule):
            return "No volume!", False

        muted = "M " if pulse_module.current_muted else " "
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
        current_volume, is_headset = self.get_pulse_data()
        now = self.get_current_time()

        return {
            "time": {"text": now},
            "mpd": {"text": mpd_now_playing, "state": state, "dur": dur, "pos": pos},
            "pacman": {"text": pacman_updates},
            "pulse": {"text": current_volume, "is_headset": is_headset},
        }

    async def main_loop(self) -> None:
        """Continuously wait for an update event, then write to serial writer."""
        while True:
            now = asyncio.get_running_loop().time()
            elapsed = now - self.last_write
            if elapsed < self.debounce_secs:
                await asyncio.sleep(self.debounce_secs - elapsed)

            line = json.dumps(self.format_status())
            self.writer.write((line + "\n").encode())
            await self.writer.drain()
            self.last_write = asyncio.get_running_loop().time()

            try:
                await asyncio.wait_for(self.update_event.wait(), timeout=self.interval_secs)
                self.update_event.clear()
            except TimeoutError:
                pass

    async def run(self) -> None:
        """Run the main loop."""
        await self.connect()
        try:
            await self.main_loop()
        finally:
            self.writer.close()
