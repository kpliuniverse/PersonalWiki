import logging
import os
import pathlib
from collections import deque
from typing import Optional, List, Deque, Dict

import attrs
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from pygments.lexers import q
from returns.result import Failure, Success

from src.itemmodels.project_item import ProjectItem
from src.wiki.wiki_items import UnnamedFolderItem, FileItem, NamedFolderItem, NamedItem, ItemType
from src.wiki.wiki_items import WikiError
from src.utils.path_utils import path_dot


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
    root_item = UnnamedFolderItem.create_root()

    queue: Deque[FolderIterEntry] = deque()
    queue.append(FolderIterEntry(
        path=root_path.relative_to(root_path),
        folder=root_item
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
    return root_item



def to_model(folder: UnnamedFolderItem):
    item_system_model = QStandardItemModel()
    root_node = item_system_model.invisibleRootItem()
    if root_node is None:
        raise Exception("item_system_model.invisibleRootItem() is None. This is not normal.")
    dir_to_item: Dict[str, QStandardItem] = dict()
    item_system_model.setHorizontalHeaderLabels([])
    subdirs: Deque[FolderIterEntry] = deque([FolderIterEntry(path_dot(), folder)])
    dot = path_dot().as_posix()
    dir_to_item[dot] = root_node
    while len(subdirs) > 0:
        subdir = subdirs.popleft()
        logging.debug("loading %s", subdir.path.as_posix())
        for child in subdir.folder.children():
            rel_subdir = subdir.path
            rel_path = rel_subdir / child.name()
            project_item = ProjectItem(rel_path)
            if child.item_type() == ItemType.FOLDER:
                subdirs.append(FolderIterEntry(rel_path, child))
                dir_to_item[rel_path.as_posix()] = project_item
                dir_to_item[rel_subdir.as_posix()].appendRow(project_item)
            if child.item_type() == ItemType.FILE:
                dir_to_item[rel_subdir.as_posix()].appendRow(project_item)
    return item_system_model
