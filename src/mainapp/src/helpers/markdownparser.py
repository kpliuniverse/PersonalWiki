import html

import mistune


def parse_markdown(md: str):
    return str(mistune.html(html.escape(md)))