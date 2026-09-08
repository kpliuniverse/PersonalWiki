import logging
import os
import pathlib
from typing import Optional, List

from src.wiki.wiki_items import UnnamedFolderItem, FileItem, NamedFolderItem, NamedItem


def walk_and_return_folder_item(root_path: pathlib.Path):
    root_folder_item = NamedFolderItem("root")
    cur_folder_stack = [root_folder_item]
    prev_path: Optional[pathlib.Path] = None
    for (path, dirnames, filenames) in os.walk(root_path):
        items: List[NamedItem] = []
        items.extend([NamedFolderItem(n) for n in dirnames])
        items.extend([FileItem(n) for n in filenames])
        items.sort(key=lambda item: item.name())
        for item in items:
            cur_folder_stack[-1].add_child(item)
