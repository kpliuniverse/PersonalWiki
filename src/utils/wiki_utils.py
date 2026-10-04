import logging
import os
import pathlib
from collections import deque
from typing import Optional, List, Deque, Dict
from uuid import UUID

import attrs
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from pygments.lexers import q
from returns.result import Failure, Success
from sqlalchemy import Connection, select
from sqlalchemy.orm import Session

from src.itemmodels.project_item import ItemInfo, ProjectItem
from src.utils.db_utils import get_directory_uuid_query, get_wikidirectory_query
from src.wiki.datamodel import WikiDirectoryEntry, WikiFileEntry, ROOT_DIR_UUID
from src.wiki.wiki_items import FolderItem, FileItem, Item, ItemType
from src.wiki.wiki_items import WikiError
from src.utils.path_utils import path_dot
from src.exceptions import WikiDatabaseError


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
    folder: FolderItem

def walk_and_return_folder_item(root_path: pathlib.Path):
    """
        Loads the widget with a specific path
    """
    root_item = FolderItem("root")

    queue: Deque[FolderIterEntry] = deque()
    queue.append(FolderIterEntry(
        path=path_dot(),
        folder=root_item
    ))

    while queue:
        cur_folder = queue.popleft()
        for path in (root_path / cur_folder.path).iterdir():
            if path.is_file():
                cur_folder.folder.add_child(FileItem(path.name))
            if path.is_dir():
                folder = FolderItem(path.name)
                cur_folder.folder.add_child(folder)
                queue.append(FolderIterEntry(
                    path=path.relative_to(root_path),
                    folder=folder
                ))
    return root_item

def iterdir_db_folder(connection: Connection, path: pathlib.Path) -> List[WikiDirectoryEntry | WikiFileEntry]:
    with Session(connection) as session:
        path_uuid = session.scalars(get_directory_uuid_query(path)).one()
        folders = session.query(WikiDirectoryEntry).where(WikiDirectoryEntry.parent_uuid == path_uuid).all()
        files = session.query(WikiFileEntry).where(WikiFileEntry.directory_uuid == path_uuid).all()
        out : List[WikiDirectoryEntry | WikiFileEntry]= [*folders, *files]
        return out

def walk_db_and_return_folder_item(connection: Connection):
    root_item = FolderItem("root")

    stack: Deque[FolderIterEntry] = deque([
        FolderIterEntry(
            path=path_dot(),
            folder=root_item
        )
    ])

    while stack:
        cur_folder = stack.pop()
        for entry in iterdir_db_folder(connection, cur_folder.path):
            if isinstance(entry, WikiFileEntry):
                cur_folder.folder.add_child(FileItem(entry.name))
            if isinstance(entry, WikiDirectoryEntry):
                folder = FolderItem(entry.name)
                cur_folder.folder.add_child(folder)
                stack.append(FolderIterEntry(
                    path=cur_folder.path / entry.name,
                    folder=folder
                ))
    return root_item
                

def to_model(folder: FolderItem):
    item_system_model = QStandardItemModel()
    root_node = item_system_model.invisibleRootItem()
    if root_node is None:
        raise ValueError("item_system_model.invisibleRootItem() is None. This is not normal.")
    dir_to_item: Dict[str, QStandardItem] = dict()
    item_system_model.setHorizontalHeaderLabels([])
    subdirs: Deque[FolderIterEntry] = deque([FolderIterEntry(path_dot(), folder)])
    dot = path_dot().as_posix()
    dir_to_item[dot] = root_node
    while len(subdirs) > 0:
        subdir = subdirs.popleft()
        #logging.debug("loading %s", subdir.path.as_posix())
        for child in subdir.folder.children():
            #print(subdir.folder)
            rel_subdir = subdir.path
            rel_path = rel_subdir / child.name()
            item_info = ItemInfo(
                path = rel_path,
                item_type=child.item_type()
            )
            project_item = ProjectItem(item_info)
            if isinstance(child, FolderItem):
                subdirs.append(FolderIterEntry(rel_path, child))
                dir_to_item[rel_path.as_posix()] = project_item
                dir_to_item[rel_subdir.as_posix()].appendRow(project_item)
            if isinstance(child, FileItem):
                dir_to_item[rel_subdir.as_posix()].appendRow(project_item)
    return item_system_model

def get_file_sess(session: Session, item: pathlib.Path):
    if item == path_dot():
        return None

    return (session.query(WikiFileEntry)
                .where(WikiFileEntry.name == item.name)
                .where(WikiFileEntry.directory_uuid == get_directory_uuid_query(item.parent).scalar_subquery())
        ).one_or_none()

def get_file(connection: Connection, item: pathlib.Path):
    with Session(connection) as session:
        return get_file_sess(session, item)


def get_dir_sess(session: Session, item: pathlib.Path):
    if item == path_dot():
        return session.get(WikiDirectoryEntry, ROOT_DIR_UUID)
    return (session.query(WikiDirectoryEntry)
            .where(WikiDirectoryEntry.name == item.name)
            .where(WikiDirectoryEntry.parent_uuid == get_directory_uuid_query(item.parent).scalar_subquery())
        ).one_or_none()
    
def get_dir(connection: Connection, item: pathlib.Path):
    with Session(connection) as session:
        return get_dir_sess(session, item)

def get_item_sess(session: Session, item: pathlib.Path):
    return get_file_sess(session, item) or get_dir_sess(session, item)

def get_item(connection: Connection, item: pathlib.Path):
    return get_file(connection, item) or get_dir(connection, item)

def ensure_get_item(connection: Connection, item: pathlib.Path):
    if (x := get_item(connection, item)) is None:
        raise WikiDatabaseError(f"Item '{item.as_posix()}' not found.")
    return x

def ensure_get_item_sess(session: Session, item: pathlib.Path):
    if (x := get_item_sess(session, item)) is None:
        raise WikiDatabaseError(f"Item '{item.as_posix}()' not found.")
    return x

def is_file(connection: Connection, item: pathlib.Path):
    return get_file(connection, item) is not None

def is_dir(connection: Connection, item: pathlib.Path):
    return get_dir(connection, item) is not None