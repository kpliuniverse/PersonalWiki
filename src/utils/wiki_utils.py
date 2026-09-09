import logging
import os
import pathlib
from typing import Optional, List

from returns.result import Failure, Success

from src.wiki.wiki_items import UnnamedFolderItem, FileItem, NamedFolderItem, NamedItem
from src.wiki.wiki_items import WikiError


def walk_and_return_folder_item(root_path: pathlib.Path):
    root_folder_item = NamedFolderItem("root")
    for (path, dirnames, filenames) in os.walk(root_path):
        path = pathlib.Path(path).relative_to(root_path)
        match root_folder_item.get_path(path):
            case Failure(e):
                if e == WikiError.ITEM_NOT_FOUND:
                    raise Exception(f"Item {path} not found")
            case Success(f):
                cur_folder = f
        items: List[NamedItem] = []
        items.extend([NamedFolderItem(n) for n in dirnames])
        items.extend([FileItem(n) for n in filenames])
        items.sort(key=lambda item: item.name())

        for item in items:
            cur_folder.add_child(item)

    return root_folder_item


