"""Modules for pysomebar."""

import asyncio
import contextlib
import socket
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from asyncinotify import Event, Inotify, Mask

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from pathlib import Path

    from pysomebar.updater import Updater


class Module(ABC):
    """Abstract base class for modules."""

    name: str

    def __init__(self, name: str = "", interval: int = 10) -> None:  # noqa: D107
        self.name = name
        self.updater: Updater | None = None
        self.interval = interval
        self.do_initial_update = True
        self.output: str = ""
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


class NeedsInternetModule(Module, ABC):
    """A module which requires an internet connection upon loading to function.

    E.g. checking a package repository for updates.
    """

    name: str

    def __init__(  # noqa: D107
        self,
        name: str = "",
        interval: int = 10,
        retry_interval: float = 1.0,
        connect_retries: int = 1,
    ) -> None:
        self.name = name
        super().__init__(name=name, interval=interval)

        for _ in range(connect_retries):
            if self.is_internet_available():
                break
            time.sleep(retry_interval)
        else:
            self.output = "No network!"

    def is_internet_available(  # noqa: D102
        self,
        host: str = "8.8.8.8",
        port: int = 53,
        timeout: int = 3,
    ) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((host, port))

        except OSError:
            return False

        else:
            return True
