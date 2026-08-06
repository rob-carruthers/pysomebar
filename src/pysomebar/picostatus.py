import contextlib
import asyncio
import datetime
import json
from typing import Literal

import serial_asyncio

from pysomebar.module import Module, MPDModule, PacmanModule
from pysomebar.module.mpd import MPDPlayerState

PicoStatusInputDataType = Literal["time", "mpd", "pacman"]


class PicoStatusUpdater:
    def __init__(
        self,
        modules: dict[str, Module],
        port: str = "/dev/ttyACM1",
        baud: int = 115200,
        interval_secs: float = 0.5,
    ) -> None:
        self.modules = modules
        self.port = port
        self.baud = baud
        self.interval = interval_secs
        self.reader: asyncio.StreamReader
        self.writer: asyncio.StreamWriter
        self.update_event = asyncio.Event()

    async def connect(self):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(
            url=self.port,
            baudrate=self.baud,
        )

    def get_mpd_data(self) -> tuple[str, MPDPlayerState, int, int]:
        mpd_module = self.modules.get("mpd")
        if not isinstance(mpd_module, MPDModule) or mpd_module.status is None:
            return "mpd not loaded", "stop", 0, 100

        status = mpd_module.status
        if status.state == "stop":
            return "Stopped", "stop", status.pos, status.dur

        now_playing = status.artist + " - " + status.title
        return now_playing, status.state, status.pos, status.dur

    def get_pacman_data(self) -> str:
        pacman_module = self.modules.get("pacman")
        if not isinstance(pacman_module, PacmanModule):
            return "No network!"

        return pacman_module.raw_output

    def format_status(self) -> dict[PicoStatusInputDataType, dict[str, str | int]]:
        now = datetime.datetime.now(tz=datetime.UTC).astimezone()
        nowstr = now.strftime("%H:%M:%S")
        mpd_now_playing, state, pos, dur = self.get_mpd_data()
        pacman_updates = self.get_pacman_data()

        return {
            "time": {"text": nowstr},
            "mpd": {"text": mpd_now_playing, "state": state, "dur": dur, "pos": pos},
            "pacman": {"text": pacman_updates},
        }

    async def run(self) -> None:
        await self.connect()
        last_write = 0.0
        try:
            while True:
                now = asyncio.get_running_loop().time()
                elapsed = now - last_write
                if elapsed < self.interval:
                    await asyncio.sleep(self.interval - elapsed)

                line = json.dumps(self.format_status())
                self.writer.write((line + "\n").encode())
                await self.writer.drain()
                last_write = asyncio.get_running_loop().time()

                try:
                    await asyncio.wait_for(self.update_event.wait(), timeout=self.interval)
                    self.update_event.clear()
                except TimeoutError:
                    pass
        finally:
            self.writer.close()
