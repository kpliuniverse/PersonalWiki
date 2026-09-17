"""
    Add HTML-style special escape tags such as <br>, <le> for '<', <ge> for '>'
"""

from mistune import Markdown


def tagstyle(md: Markdown):
    md.inline.register("escape", "<.*>", parse_escape)