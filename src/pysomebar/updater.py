"""Main entry point for pysomebar."""

import asyncio
import contextlib
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles

from pysomebar.config import CONFIG
from pysomebar.util import make_dwlb_colored_text

if TYPE_CHECKING:
    from .module import Module


class Updater(ABC):
    """Orchestrator for updater.

    Contains Modules and handles writing to output.

    Should be subclassed for a specific implementation (e.g. `somebar`, `dwlb`...)
    """

    def __init__(self) -> None:  # noqa: D107
        self.separator = CONFIG.separator
        self.padding = CONFIG.edge_padding
        self.modules: list[Module] = []
        self.output: str = ""
        self.last_output: str = ""
        self.update_event = asyncio.Event()
        self.tasks: set[asyncio.Task] = set()

    async def add_module(self, module: Module) -> None:
        """Add a module to this updater."""
        if not module.enabled:
            return

        module.updater = self
        self.tasks.add(asyncio.create_task(module.loop()))
        self.modules.append(module)

    def assemble_output(self) -> str:
        """Assemble output from modules."""
        joined_output = self.separator.join(module.output for module in self.modules)

        return " " * self.padding + joined_output + " " * self.padding

    @abstractmethod
    async def write_output(self) -> None:
        """Write output to bar."""

    async def initial_update(self) -> None:
        """Initialise state/output for all held modules."""
        if len(self.modules) < 1:
            return

        for module in self.modules:
            if not module.do_initial_update:
                continue
            await module.update()

        await self.write_output()

    async def loop(self) -> None:
        """Continuously wait for updates/interval timeouts and write to named pipe."""
        if len(self.modules) < 1:
            return

        while True:
            await self.update_event.wait()
            await asyncio.sleep(0)
            await self.write_output()


class SomebarUpdater(Updater):
    """Updater for `somebar`.

    Updates somebar via its named pipe in $XDG_RUNTIME_DIR. An update is performed by writing a
    string beginning "status " to the pipe, followed by the bar text and a newline.
    """

    def __init__(self) -> None:  # noqa: D107
        super().__init__()
        xdg_runtime_dir = os.environ["XDG_RUNTIME_DIR"]
        self.somebar = Path(xdg_runtime_dir) / "somebar-0"

        retries = 10
        for _ in range(retries):
            if self.somebar.exists():
                break
            time.sleep(0.5)
        else:
            raise FileNotFoundError

    async def write_output(self) -> None:
        """Write output to somebar's named pipe."""
        joined_output = self.assemble_output()

        if joined_output != self.last_output:
            with contextlib.suppress(BrokenPipeError):
                async with aiofiles.open(self.somebar, "w") as f:
                    status = f"status {joined_output}\n"
                    await f.write(status)

                self.last_output = joined_output

        self.update_event.clear()


class DwlbUpdater(Updater):
    """Updater for `dwlb`.

    Usually dwlb will be initialised via `dwl -s dwlb`. `pysomebar` should then be piped into
    another instance of dwlb, which will update status on stdout write. i.e.:

    uv run pysomebar | dwlb -status-stdin all
    """

    def __init__(self) -> None:  # noqa: D107
        super().__init__()
        self.separator = make_dwlb_colored_text(self.separator, fg=CONFIG.separator_color)

    async def write_output(self) -> None:
        """Write output to stdout."""
        joined_output = self.assemble_output()

        if joined_output != self.last_output:
            with contextlib.suppress(BrokenPipeError):
                print(joined_output, flush=True)  # noqa: T201
                self.last_output = joined_output

        self.update_event.clear()
