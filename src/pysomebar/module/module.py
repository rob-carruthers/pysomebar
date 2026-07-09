"""Modules for pysomebar."""

import asyncio
import contextlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from asyncinotify import Event, Inotify, Mask

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from pysomebar.updater import Updater


class Module(ABC):
    """Abstract base class for modules."""

    def __init__(self, interval: int) -> None:  # noqa: D107
        self.updater: Updater | None = None
        self.interval = interval
        self.do_initial_update = True
        self.output: str = ""
        self.enabled: bool = False
        self.refresh_signal: int | None = None
        self.refresh_event = asyncio.Event()

    def request_refresh(self) -> None:
        """Signal this module to refresh immediately, bypassing its interval wait."""
        self.refresh_event.set()

    @abstractmethod
    async def update(self) -> None:
        """Abstract method for updating asynchronously."""
        ...

    async def loop(self) -> None:
        """Loop over interval/async updates."""
        if not self.enabled:
            return

        while True:
            try:
                await asyncio.wait_for(self.update(), timeout=self.interval)
            except asyncio.TimeoutError:  # noqa: UP041
                continue

            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self.refresh_event.wait(), timeout=self.interval)
            self.refresh_event.clear()

    @staticmethod
    async def watch_files(
        *files: Path,
        mask: Mask = Mask.MODIFY,
    ) -> AsyncGenerator[Event]:
        """Watch inotify events on `files`, yielding an async generator of events.

        If an element of `files` is a dir, watch events on that dir. If a file, set up an inotify
        watch on the parent dir and filter the dir's events to match only files in `files`.

        Parameters
        ----------
        *files : Path
            The file(s)/dir(s) to watch.

        mask : asyncinotify.Mask
            The mask of events to watch for.

        """
        watch_dirs = {file for file in files if file.is_dir()}
        watch_files_ = {file for file in files if not file.is_dir()}
        parent_dirs = {file.parent for file in watch_files_}

        with Inotify() as inotify:
            for dir_ in watch_dirs | parent_dirs:
                inotify.add_watch(dir_, mask)

            async for event in inotify:
                if event.path is None:
                    continue
                if event.path in watch_files_ or event.path.parent in watch_dirs:
                    yield event
