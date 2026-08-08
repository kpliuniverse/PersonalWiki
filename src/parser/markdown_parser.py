from mistune import create_markdown

from src.parser.custom_renderer import CustomHTMLRenderer

def parse_chunk(md: str):
    ##TODO: deal with external links
    return str(create_markdown(
        renderer=CustomHTMLRenderer(),
        escape=True,
        plugins=["strikethrough", "footnotes", "table"]
    )(md))