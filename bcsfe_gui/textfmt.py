"""Turns BCSFE's colour-tagged text (<@p>, <@e>, </>...) into [text, style]
segments that the web interface paints with its own palette."""

from __future__ import annotations

import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# BCSFE theme tags -> short style names understood by the CSS.
THEME_TAGS = {
    "@p": "p",
    "@s": "s",
    "@t": "t",
    "@q": "q",
    "@e": "e",
    "@w": "w",
    "@su": "su",
}

# Named colours, darkened where needed so they are readable on a light background.
NAMED_COLORS = {
    "green": "#2e9d3a", "g": "#2e9d3a",
    "red": "#d93025", "r": "#d93025",
    "dark_yellow": "#b8860b", "dy": "#b8860b",
    "black": "#000000", "bl": "#000000",
    "white": "#9a9a9a", "w": "#9a9a9a",
    "cyan": "#008b9a", "c": "#008b9a",
    "dark_grey": "#6b6b6b", "dg": "#6b6b6b",
    "blue": "#1a56db", "b": "#1a56db",
    "yellow": "#c99700", "y": "#c99700",
    "magenta": "#b5179e", "m": "#b5179e",
    "dark_blue": "#00008b", "db": "#00008b",
    "dark_cyan": "#008b8b", "dc": "#008b8b",
    "dark_magenta": "#8b008b", "dm": "#8b008b",
    "dark_red": "#8b0000", "dr": "#8b0000",
    "dark_green": "#006400", "dgn": "#006400",
    "light_grey": "#8a8a8a", "lg": "#8a8a8a",
    "orange": "#e07b00", "o": "#e07b00",
}


def _special_chars() -> list[str]:
    try:
        from bcsfe import core

        return core.LocalManager.get_special_chars()
    except Exception:
        return ["<", ">", "/"]


def _tag_style(tag: str) -> str:
    if not tag:
        return ""
    if tag in THEME_TAGS:
        return THEME_TAGS[tag]
    if tag.startswith("#"):
        return tag
    if tag.startswith("@"):
        return "p"
    return NAMED_COLORS.get(tag.lower(), "")


def parse(text: str) -> list[list[str]]:
    """Same parser as bcsfe.cli.color, but it returns the tag instead of an
    ANSI colour so the colours can be adapted to the interface."""
    text = ANSI_RE.sub("", str(text))
    txt = "<@p>" + text + "</>"
    output: list[list[str]] = []
    tags: list[str] = []
    inside_tag = False
    in_closing_tag = False
    tag_text = ""
    buf = ""
    special_chars = _special_chars()
    i = 0
    while i < len(txt):
        char = txt[i]
        if char == "\\" and i + 1 < len(txt) and txt[i + 1] in special_chars:
            buf += txt[i + 1]
            i += 2
            continue
        tag = tags[-1] if tags else ""
        if char == ">" and inside_tag:
            inside_tag = False
            if not in_closing_tag:
                tags.append(tag_text)
            in_closing_tag = False
            tag_text = ""
        if char == "<" and not inside_tag:
            inside_tag = True
            if buf:
                output.append([buf, _tag_style(tag)])
                buf = ""
            tag_text = ""
        if char == "/" and inside_tag:
            in_closing_tag = True
            if tags:
                tags.pop()
        if not inside_tag and char not in "<>":
            buf += char
        if inside_tag and char not in "<>":
            tag_text += char
        i += 1
    if buf:
        output.append([buf, _tag_style(tags[-1] if tags else "")])
    return output


def plain(text: str) -> str:
    return "".join(seg[0] for seg in parse(text))
