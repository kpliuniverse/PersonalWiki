from typing import Callable, List

from mistune import Markdown, create_markdown
from mistune.plugins.table import table
from mistune.plugins.footnotes import footnotes
from src.mistune_plugins.special_tags import special_tags
from src.renderer.custom_renderer import CustomHTMLRenderer



def add_plugins(md: Markdown, plugins: List[Callable[[Markdown]]]):
    for plugin in plugins:
        plugin(md)

def parse_md(md: str):

    plugins: List[Callable[[Markdown]]] = [
        table,
        footnotes,
        special_tags
    ]
    
    md_instance = create_markdown(
        renderer=CustomHTMLRenderer(),
        escape=True,
        
    )
    add_plugins(md_instance, plugins)
    return str(md_instance(md))