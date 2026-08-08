from dataclasses import dataclass
import pathlib

from src.wiki.wiki import Wiki

class AppState:
    cur_wiki: Wiki
    