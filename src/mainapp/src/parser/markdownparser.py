import html

import mistune


def parse_markdown(md: str):
    ##TODO: deal with external links
    return str(mistune.html(html.escape(md)))