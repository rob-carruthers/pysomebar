import asyncio
import datetime
import json
from typing import Literal

import serial_asyncio

from pysomebar.module import Module, MPDModule, PacmanModule

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

    async def connect(self):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(
            url=self.port,
            baudrate=self.baud,
        )

    def get_mpd_data(self) -> tuple[str, int, int]:
        mpd_module = self.modules.get("mpd")
        if not isinstance(mpd_module, MPDModule) or mpd_module.status is None:
            return "mpd not loaded", 0, 100

        status = mpd_module.status
        if status.state == "stop":
            return "Stopped", status.pos, status.dur

        now_playing = status.artist + " - " + status.title
        return now_playing, status.pos, status.dur

    def get_pacman_data(self) -> str:
        pacman_module = self.modules.get("pacman")
        if not isinstance(pacman_module, PacmanModule):
            return "No network!"

        return pacman_module.raw_output

    def format_status(self) -> dict[PicoStatusInputDataType, dict[str, str | int]]:

        now = datetime.datetime.now(tz=datetime.UTC).astimezone()
        nowstr = now.strftime("%H:%M:%S")
        mpd_now_playing, pos, dur = self.get_mpd_data()
        pacman_updates = self.get_pacman_data()

        return {
            "time": {"text": nowstr},
            "mpd": {"text": mpd_now_playing, "dur": dur, "pos": pos},
            "pacman": {"text": pacman_updates},
        }

    async def run(self) -> None:
        await self.connect()
        try:
            while True:
                line = json.dumps(self.format_status())
                self.writer.write((line + "\n").encode())
                await self.writer.drain()
                await asyncio.sleep(self.interval)
        finally:
            self.writer.close()
