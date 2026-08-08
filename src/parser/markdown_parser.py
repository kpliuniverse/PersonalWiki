from typing import Callable, List

from mistune import Markdown, create_markdown
from mistune.plugins.table import table
from src.parser.custom_renderer import CustomHTMLRenderer



def add_plugins(md: Markdown, plugins: List[Callable[[Markdown]]]):
    for plugin in plugins:
        plugin(md)

def parse_chunk(md: str):

    plugins: List[Callable[[Markdown]]] = [
        table
    ]
    md_instance = create_markdown(
        renderer=CustomHTMLRenderer(),
        escape=True,
        
    )
    add_plugins(md_instance, plugins)
    ##TODO: deal with external links
    return str(md_instance(md))