import os
import pathlib

from src.wiki.wiki_items import FolderItem


def walk_and_return_folder_item(path: pathlib.Path):
    for (path, dirnames, filenames) in os.walk(path):
        path = pathlib.Path(path)
        root = path.name
        print(f"{path=}{dirnames=}{filenames=}")