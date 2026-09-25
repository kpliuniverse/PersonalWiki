from dataclasses import dataclass
import pathlib

from src.states.wikistate import WikiState
from src.wiki.wiki import Wiki

class AppState:
    cur_wiki: Wiki

@dataclass
class PickleableAppState:
    wiki_state: WikiState

def to_pickleable(app_state: AppState):
    return PickleableAppState(
        wiki_state=app_state.cur_wiki.get_wiki_state()
    )