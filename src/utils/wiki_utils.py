import logging
import os
import pathlib
from collections import deque
from typing import Optional, List, Deque

import attrs
from pygments.lexers import q
from returns.result import Failure, Success

from src.wiki.wiki_items import UnnamedFolderItem, FileItem, NamedFolderItem, NamedItem
from src.wiki.wiki_items import WikiError


# def walk_and_return_folder_item(root_path: pathlib.Path):
#     root_folder_item = NamedFolderItem("root")
#     for (path, dirnames, filenames) in os.walk(root_path):
#         path = pathlib.Path(path).relative_to(root_path)
#         match root_folder_item.get_path(path):
#             case Failure(e):
#                 if e == WikiError.ITEM_NOT_FOUND:
#                     raise Exception(f"Item {path} not found")
#             case Success(f):
#                 cur_folder = f
#         items: List[NamedItem] = []
#         items.extend([NamedFolderItem(n) for n in dirnames])
#         items.extend([FileItem(n) for n in filenames])
#         items.sort(key=lambda item: item.name())

#         for item in items:
#             cur_folder.add_child(item)

#     return root_folder_item.to_unnamed_folder_item()
@attrs.define
class FolderIterEntry:
    path: pathlib.Path
    folder: UnnamedFolderItem

def walk_and_return_folder_item(root_path: pathlib.Path):
    """
        Loads the widget with a specific path
    """
    # TODO: separate file scanning logic
    root_node = UnnamedFolderItem("root")

    queue: Deque[FolderIterEntry] = deque()
    queue.append(FolderIterEntry(
        path=root_path.relative_to(root_path),
        folder=root_node
    ))
    while queue:
        cur_folder = queue.popleft()
        for path in (root_path / cur_folder.path).iterdir():
            if path.is_file():
                cur_folder.folder.add_child(FileItem(path.name))
            if path.is_dir():
                folder = UnnamedFolderItem(path.name)
                cur_folder.folder.add_child(folder)
                queue.append(FolderIterEntry(
                    path=path.relative_to(root_path),
                    folder=folder
                ))
    root_node.print()