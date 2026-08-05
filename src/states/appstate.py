from dataclasses import dataclass
import pathlib

@dataclass
class AppState:
    cur_wiki: pathlib.Path
    cur_file: pathlib.Path