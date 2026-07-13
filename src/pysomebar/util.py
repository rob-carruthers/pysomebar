"""Utility methods."""

import re

from pysomebar.config import CONFIG


def format_bytes(b: float, base: int = 1024) -> str:
    """Format n bytes output to B/K/M/G.

    If G, then round to 1dp, otherwise round to nearest integer.
    """
    round_n = None
    if b < base:
        return f"{round(b, round_n)}B"
    if b < (base**2):
        return f"{round(b / base, round_n)}K"
    if b < (base**3):
        return f"{round(b / base**2, round_n)}M"

    round_n = 1
    return f"{round(b / base**3, round_n)}G"


def make_dwlb_colored_text(text: str, *, fg: str = "", bg: str = "") -> str:
    """Attach beginning and terminating color tags to `text` for dwlb output."""
    # Look up colors from config if not already hex colors.
    # If field is already empty string, leave it empty
    # If a lookup was needed but didn't exist, default to #ffffff.
    if fg and not fg.startswith("#"):
        fg = CONFIG.colors.get(fg, "#ffffff")
    if bg and not bg.startswith("#"):
        bg = CONFIG.colors.get(bg, "#ffffff")

    for field in (fg, bg):
        if field and not re.match(r"#[0-9a-fA-F]{6}", field):
            msg = "`color` is not a valid hex color."
            raise ValueError(msg)

    fg = fg.replace("#", "")
    bg = bg.replace("#", "")

    output = ""

    if fg:
        output += f"^fg({fg})"
    if bg:
        output += f"^bg({bg})"

    output += text

    if fg:
        output += "^fg()"
    if bg:
        output += "^bg()"

    return output
