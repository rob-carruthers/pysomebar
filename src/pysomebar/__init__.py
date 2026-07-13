"""Main entry point for pysomebar."""

import asyncio
import contextlib
import os
import signal
import sys
from pathlib import Path

from pysomebar.config import CONFIG

from .module import (
    BatteryModule,
    BrightnessModule,
    DateModule,
    MemoryModule,
    Module,
    MPDModule,
    PacmanModule,
    PortageModule,
    PulseModule,
    TempModule,
)
from .updater import DwlbUpdater, SomebarUpdater

PID_FILE = "pysomebar.pid"


def write_pid_file() -> Path:
    """Write file containing current PID to XDG_RUNTIME_DIR."""
    pid = os.getpid()
    pid_path = Path(os.environ["XDG_RUNTIME_DIR"]) / PID_FILE

    if pid_path.exists():
        msg = "PID file exists - is another instance running?"
        raise RuntimeError(msg)

    with pid_path.open("w") as f:
        f.write(str(pid))

    return pid_path


async def main_loop() -> None:
    """Start main async loop."""
    # Set an event handler for SIGPIPE if using piped stdout - shutdown if the pipe is destroyed
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    loop.add_signal_handler(signal.SIGPIPE, stop_event.set)

    match CONFIG.bar_type:
        case "somebar":
            updater = SomebarUpdater()
        case "dwlb":
            updater = DwlbUpdater()

    await updater.add_module(MPDModule())
    await updater.add_module(MemoryModule())
    await updater.add_module(PulseModule())
    await updater.add_module(BrightnessModule())
    await updater.add_module(TempModule())
    await updater.add_module(BatteryModule())
    await updater.add_module(PacmanModule())
    await updater.add_module(PortageModule())
    await updater.add_module(DateModule())

    signal_groups: dict[int, list[Module]] = {}
    for module in updater.modules:
        if module.refresh_signal is not None:
            signal_groups.setdefault(module.refresh_signal, []).append(module)

    for offset, modules in signal_groups.items():

        def handle_refresh(modules: list[Module] = modules) -> None:
            for module in modules:
                module.request_refresh()

        loop.add_signal_handler(signal.SIGRTMIN + offset, handle_refresh)

    await updater.initial_update()
    updater_task = asyncio.create_task(updater.loop())

    await stop_event.wait()
    updater_task.cancel()

    for task in updater.tasks:
        task.cancel()
    await asyncio.gather(updater_task, *updater.tasks, return_exceptions=True)


def main() -> None:  # noqa: D103
    # Safety net - broken pipe is handled in write_output()
    pid_path = write_pid_file()
    try:
        with contextlib.suppress(KeyboardInterrupt, BrokenPipeError):
            asyncio.run(main_loop())
    finally:
        pid_path.unlink(missing_ok=True)

    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())
