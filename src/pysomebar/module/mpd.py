"""MPD module for pysomebar."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import ClassVar, Literal

import mpd
from mpd.asyncio import MPDClient

from pysomebar.config import CONFIG

from .module import Module

MPDPlayerState = Literal["play", "stop", "pause"]


@dataclass(kw_only=True)
class MPDStatus:
    """Status information for an MPD status poll."""

    state: MPDPlayerState
    song: int | None
    artist: str
    title: str

    _STATE_ICONS: ClassVar[dict[MPDPlayerState, str]] = {
        "play": "",
        "stop": "󰓛",
        "pause": "󰏤",
    }

    def __post_init__(self) -> int | None:  # noqa: D105
        self.song = None if self.song is None else int(self.song)

    @property
    def state_icon(self) -> str:
        """Return the appropriate icon corresponding to self.state."""
        return self._STATE_ICONS[self.state]

    @classmethod
    async def from_client(cls, client: MPDClient) -> MPDStatus:
        """Create an MPDStatus from MPDClient polls to status() and playlistinfo()."""
        s = await client.status()  # ty:ignore[unresolved-attribute]
        song = s.get("song")
        if song is not None:
            now_playing = await client.playlistinfo(song)  # ty:ignore[unresolved-attribute]
        else:
            return MPDStatus(state=s["state"], song=song, artist="Stopped", title="Stopped")

        if len(now_playing) == 0:
            return MPDStatus(state=s["state"], song=song, artist="Stopped", title="Stopped")

        now_playing = now_playing[0]
        return MPDStatus(
            state=s["state"],
            song=song,
            artist=now_playing.get("artist", "Unknown"),
            title=now_playing.get("title", "Unknown"),
        )


class MPDModule(Module):
    """Module for monitoring MPD."""

    name = "mpd"

    def __init__(self) -> None:  # noqa: D107
        super().__init__(name=self.name, interval=CONFIG.mpd.interval)

        self.enabled = CONFIG.mpd.enabled
        self.do_initial_update = False
        self.client = MPDClient()
        self.connect_retries = 10

    async def connect(self) -> None:
        """Connect to MPD if not already connected."""
        if self.client.connected:
            return

        await self.client.connect(host=CONFIG.mpd.host, port=CONFIG.mpd.port)

    async def update(self) -> None:
        """Passthrough as we handle everything in loop()."""

    async def make_output(self) -> None:
        """Make output from volume and mute status."""
        status = await MPDStatus.from_client(self.client)

        if status.state == "stop":
            self.output = f"{status.state_icon}"
        else:
            self.output = f"{status.state_icon} {status.artist} - {status.title}"

        if self.updater is not None:
            self.updater.update_event.set()

    async def ensure_connected(self) -> bool:
        """Try to (re)connect to MPD, retrying with backoff. Returns True on success."""
        if self.client.connected:
            return True
        for _ in range(self.connect_retries):
            try:
                await self.connect()
            except (ConnectionRefusedError, OSError, mpd.base.MPDError):
                await asyncio.sleep(CONFIG.try_reconnect_interval)
            else:
                return True
        return False

    async def loop(self) -> None:
        """Update output with current date/time in chosen format."""
        if not self.enabled:
            return

        while True:
            if not await self.ensure_connected():
                self.output = "connection error"
                if self.updater is not None:
                    self.updater.update_event.set()
                await asyncio.sleep(self.interval)
                continue

            try:
                await self.make_output()
                async for _ in self.client.idle():
                    await self.make_output()

            except (ConnectionResetError, BrokenPipeError, OSError, mpd.base.MPDError):
                with contextlib.suppress(Exception):
                    self.client.disconnect()
                await asyncio.sleep(CONFIG.try_reconnect_interval)
