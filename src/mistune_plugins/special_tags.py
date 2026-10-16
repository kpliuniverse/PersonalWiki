"""
    Add HTML-style special escape tags such as <br>, <le> for '<', <ge> for '>'
"""

from html import escape
import logging
from typing import Any, Match

from mistune import InlineParser, InlineState, Markdown


ESCAPE_DICT: dict[str, str] = {
    "br": "\n",
    "lt": "<",
    "gt": ">",
}
def parse_escapes(inline: InlineParser, m: Match[str], state: InlineState) -> int:
    esc: str | Any = m.group("tag").strip()
    value: str = ESCAPE_DICT.get(esc, f"[Unknown escape: {esc}]")

    if value == "\n":
        state.append_token({
            "type": "line_break"
        })
    else:
        state.append_token({
            "type": "text",
            "raw": value
        })
    return m.end()

def special_tags(md: Markdown) -> None:
    md.inline.register("special_tags", r"<(?P<tag>.*?)>", parse_escapes, before="inline_html")
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("line_break", lambda _: "<br>")