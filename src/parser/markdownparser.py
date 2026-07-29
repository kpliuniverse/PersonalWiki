from mistune import create_markdown

from src.parser.customrenderer import CustomHTMLRenderer

def parse_chunk(md: str):
    ##TODO: deal with external links
    return create_markdown(renderer=CustomHTMLRenderer(), escape=True,plugins=["strikethrough", "footnotes", "table"])(md)