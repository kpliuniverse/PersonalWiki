

import pathlib
import shutil

from src.wiki.wiki import create_wiki


def main():
    testenv_path = pathlib.Path(".testenv")
    if testenv_path.exists():
        shutil.rmtree(testenv_path)
    testenv_path.mkdir()
    create_wiki(testenv_path, "new")