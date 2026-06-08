import os
import random
from pathlib import Path

XDG_RUNTIME_DIR = os.environ["XDG_RUNTIME_DIR"]
SOMEBAR = Path(XDG_RUNTIME_DIR) / "somebar-0"
RETRIES = 10


def main() -> None:
    for _ in range(RETRIES):
        if SOMEBAR.exists():
            break
    else:
        raise FileNotFoundError

    with SOMEBAR.open("w") as f:
        f.write(f"status hi {random.randint(0, 10)}\n")
