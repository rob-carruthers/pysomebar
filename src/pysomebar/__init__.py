import os
import random
from pathlib import Path

from .module import DateModule, Module

XDG_RUNTIME_DIR = os.environ["XDG_RUNTIME_DIR"]
SOMEBAR = Path(XDG_RUNTIME_DIR) / "somebar-0"
RETRIES = 10


class SomebarUpdater:
    def __init__(self, separator: str = " | "):
        self.separator = separator
        self.modules: list[Module] = []
        self.output: str = ""
        self.last_output: str = ""

    def write_output(self):
        joined_output = " | ".join(module.output for module in self.modules)
        with SOMEBAR.open("w") as f:
            f.write(f"status {joined_output}\n")

    def initial_update(self):
        [module.update() for module in self.modules]


def main() -> None:
    for _ in range(RETRIES):
        if SOMEBAR.exists():
            break
    else:
        raise FileNotFoundError

    updater = SomebarUpdater()
    updater.modules.append(DateModule(5))
    updater.initial_update()
    updater.write_output()
