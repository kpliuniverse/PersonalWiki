"""
    Add HTML-style special escape tags such as <br>, <le> for '<', <ge> for '>'
"""

from html import escape
import logging
from typing import Match

from mistune import InlineParser, InlineState, Markdown


ESCAPE_DICT = {
    "br": "\n",
    "lt": "<",
    "gt": ">",
}
def parse_escapes(inline: InlineParser, m: Match[str], state: InlineState):
    esc = m.group("tag").strip()
    value = ESCAPE_DICT.get(esc, f"[Unknown escape: {esc}]")

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

def special_tags(md: Markdown):
    md.inline.register("special_tags", r"<(?P<tag>.*?)>", parse_escapes, before="inline_html")
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("line_break", lambda _: "<br>")