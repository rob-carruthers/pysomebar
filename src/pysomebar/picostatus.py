import asyncio
import datetime
import json

import serial_asyncio


class PicoStatusUpdater:
    def __init__(
        self,
        port: str = "/dev/ttyACM1",
        baud: int = 115200,
        interval_secs: float = 0.5,
    ):
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

    def format_status(self) -> str:

        now = datetime.datetime.now(tz=datetime.UTC).astimezone()
        nowstr = now.strftime("%H:%M:%S")

        return {
            "time": {"text": nowstr},
            "mpd": {"text": "EA Games Soundtrack - Lakuwani", "dur": "191", "pos": "126"},
            "pacman": {"text": "6 updates"},
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
