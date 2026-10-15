"""Main entry point for pysomebar."""

import asyncio
import contextlib
import inspect
import os
import signal
import sys
from pathlib import Path

from pysomebar.config import CONFIG
from pysomebar.util import (
    make_dwlb_colored_text,
    make_pango_colored_text,
    make_polybar_colored_text,
)

from .module import Module
from .updater import PipeOutputUpdater, SomebarUpdater, Updater

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


def _all_concrete_subclasses(cls: type[Module]) -> set[type[Module]]:
    result = set()
    for sub in cls.__subclasses__():
        if not inspect.isabstract(sub):
            result.add(sub)
        result |= _all_concrete_subclasses(sub)
    return result


async def instantiate_modules(updater: Updater) -> None:
    """Instantiate modules in `updater` using ordered list from config."""
    available_modules: dict[str, type[Module]] = {}
    for module_cls in _all_concrete_subclasses(Module):
        # Check for duplicated name (for new/development modules)
        if module_cls.name in available_modules:
            existing = available_modules[module_cls.name]
            msg = (
                f"Duplicate module name {module_cls.name!r}: "
                f"used by both {existing.__name__} and {module_cls.__name__}"
            )
            raise ValueError(msg)

        available_modules[module_cls.name] = module_cls

    for module_name in CONFIG.modules:
        if module_name not in available_modules:
            msg = f"Module `{module_name}` unrecognised."
            raise ValueError(msg)
        module_cls = available_modules[module_name]
        await updater.add_module(module_cls(updater.coloriser))


def create_updater() -> Updater:
    """Instantiate the relevant updater based on config."""
    picostatus = CONFIG.picostatus

    match CONFIG.bar_type:
        case "somebar":
            return SomebarUpdater(picostatus=picostatus)
        case "dwlb":
            return PipeOutputUpdater(picostatus=picostatus, coloriser=make_dwlb_colored_text)
        case "waybar":
            return PipeOutputUpdater(picostatus=picostatus, coloriser=make_pango_colored_text)
        case "polybar":
            return PipeOutputUpdater(picostatus=picostatus, coloriser=make_polybar_colored_text)
        case _:
            msg = f"bar_type `{CONFIG.bar_type}` unsupported."
            raise ValueError(msg)


def register_signal_handlers(
    loop: asyncio.AbstractEventLoop,
    updater: Updater,
    stop_event: asyncio.Event,
) -> None:
    """Register process signal handlers."""
    loop.add_signal_handler(signal.SIGPIPE, stop_event.set)

    signal_groups: dict[int, list[Module]] = {}
    for module in updater.modules.values():
        if module.refresh_signal is not None:
            signal_groups.setdefault(module.refresh_signal, []).append(module)

    for offset, modules in signal_groups.items():

        def handle_refresh(modules: list[Module] = modules) -> None:
            for module in modules:
                module.request_refresh()

        loop.add_signal_handler(signal.SIGRTMIN + offset, handle_refresh)


async def main_loop() -> None:
    """Start main async loop."""
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    updater = create_updater()
    await instantiate_modules(updater)
    register_signal_handlers(loop, updater, stop_event)

    await updater.initial_update()

    tasks: list[asyncio.Task[None]] = [asyncio.create_task(updater.loop()), *updater.tasks]

    if updater.picostatus:
        tasks.append(asyncio.create_task(updater.picostatus.run()))

    try:
        await stop_event.wait()
    finally:
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)


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
