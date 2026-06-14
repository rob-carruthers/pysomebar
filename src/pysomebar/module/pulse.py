"""Pulseaudio volume module for pysomebar."""

import asyncio
from types import MappingProxyType

import pulsectl_asyncio
from pulsectl.pulsectl import PulseError, PulseSinkInfo

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

from .module import Module


class PulseModule(Module):
    """Module for monitoring volume via Pulseaudio API."""

    vol_muted_icon = ""
    vol_icons = MappingProxyType({70: "", 40: "", -1: ""})

    def __init__(self) -> None:  # noqa: D107
        super().__init__(CONFIG.pulse.interval)

        self.enabled = CONFIG.pulse.enabled
        self.do_initial_update = False
        self.pulse = pulsectl_asyncio.PulseAsync("pysomebar-pulse")
        self.connect_retries = 10

        self.current_volume: int = -1
        self.current_muted: bool = False

    async def connect(self) -> None:
        """Connect to pulseaudio if not already connected."""
        if self.pulse.connected:
            return

        await self.pulse.connect()

    async def get_volume(self) -> tuple[int, bool]:
        """Return volume and mute status from default sink.

        Returns
        -------
        int
            Volume (as integer)
        bool
            Muted status (True: muted)

        """
        default_sink_name = (await self.pulse.server_info()).default_sink_name
        sinks: list[PulseSinkInfo] = await self.pulse.sink_list()

        default_sink = next(sink for sink in sinks if sink.name == default_sink_name)  # ty:ignore[unresolved-attribute]
        raw_vol = float(default_sink.volume.values[0])
        volume = round(raw_vol * 100)
        muted = bool(getattr(default_sink, "mute", True))

        return volume, muted

    async def update(self) -> None:
        """Passthrough as we handle everything in loop()."""

    async def make_output(self) -> None:
        """Make output from volume and mute status."""
        if self.current_muted:
            self.output = f"{self.vol_muted_icon} {self.current_volume}% (muted)"
        else:
            icon = next(
                icon for thresh, icon in self.vol_icons.items() if self.current_volume >= thresh
            )
            self.output = f"{icon} {self.current_volume}%"

        if CONFIG.bar_type == "dwlb" and self.current_muted:
            self.output = make_dwlb_colored_text(self.output, fg=CONFIG.pulse.mute_color)

        if self.updater is not None:
            self.updater.update_event.set()

    async def loop(self) -> None:
        """Update output with current date/time in chosen format."""
        if not self.enabled:
            return

        for _ in range(self.connect_retries):
            try:
                await self.connect()
                break
            except PulseError:
                await asyncio.sleep(0.5)

        else:
            self.output = "connection error"
            if self.updater is not None:
                self.updater.update_event.set()
            raise ConnectionError

        self.current_volume, self.current_muted = await self.get_volume()
        await self.make_output()

        async for event in self.pulse.subscribe_events("all"):
            if event.facility != "sink":
                continue

            volume, muted = await self.get_volume()

            if volume == self.current_volume and muted == self.current_muted:
                continue

            self.current_volume = volume
            self.current_muted = muted

            await self.make_output()
