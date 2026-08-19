import pathlib

from src.consts import WIKI_ENCODING


# i don't know what type to use without restricting to pathlib.Path
def create_empty_file(path):
    with open(path, "x", encoding=WIKI_ENCODING):
        pass
