import logging
import pathlib
from enum import IntEnum, auto, StrEnum
from typing import Any, Deque, List, Protocol, Self, Union, Optional, Callable

import attrs
from returns.result import Result, Failure, Success

from src.utils.path_utils import path_dot

class WikiError(StrEnum):
    DUPLICATE_FILE_NAME = auto()
    ITEM_NOT_FOUND = auto()
    NOT_A_DIRECTORY_ITEM = auto()

class ItemType(IntEnum):
    FILE = 0
    DIRECTORY = 1


@attrs.define
class FlatItemEntry:
    """
        Used for comparisons.
    """
    path: pathlib.Path
    type:  ItemType

class Item:
    _item_type: ItemType
    def __init__(self, name: str):
        self.__name = name

    def name(self):
        return self.__name

    def item_type(self):
        return self._item_type

    def __hash__(self):
        return hash(self.__name)



class FileItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self._item_type = ItemType.FILE

@attrs.define
class FilterFolder:
    orig: FolderItem
    filtered: FolderItem

def sort_alphabetically_key(n: Item):
    return n.name()


class FolderItem(Item):
    """
        An item that contains child items that are stored in a list.
    """
    def __init__(self, name: str, *items: Item):
        super().__init__(name)
        self._item_type = ItemType.DIRECTORY
        self.__children: List[Item] = list(items)

    def add_child(self, child: Item) -> Result[None, WikiError]:
        if child in self.__children:
            return Failure(WikiError.DUPLICATE_FILE_NAME)

        self.__children.append(child)
        return Success(None)

    def to_flat_list(self, __dir: pathlib.Path = path_dot()):
        """
            Converts to list of FlatItemEntry
            Is used for comparisons

        Print the item
        Do not use the prefix argument, it's for internal purposes
        """
        # TODO: make this non-recursive
        disp_path = __dir / self.name()
        out: List[FlatItemEntry] = [FlatItemEntry(path=disp_path, type=self.item_type())]
        for child in self.__children:
            if isinstance(child, FileItem) or (isinstance(child, FolderItem) and not child.children()):
                out.append(FlatItemEntry(
                        path=disp_path / child.name(),
                        type=child.item_type()
                    )
                )
            if isinstance(child, FolderItem):
                out.extend(child.to_flat_list(disp_path))
        return out

    def to_str_list(self):
        return [item.path.as_posix() for item in self.to_flat_list()]
    
    def __str__(self):
        return "\n".join(self.to_str_list())
        
    def __eq__(self, other):
        return isinstance(other, FolderItem) and self.to_flat_list() == other.to_flat_list()
    
    def children(self) -> List[Item]:
        return self.__children

    def folder_filter(self, cond: Callable[[FolderItem], bool], *, include_files, dont_include_children_if_parent_is_filtered_out=False):
        """
            Filters folders based on criteria.

            `include_files` determine if files should be included
        """
        root = self.create_root()

        for child in self.children():
            if isinstance(child, FileItem) and include_files:
                root.add_child(FileItem(child.name()))
            if isinstance(child, FolderItem):
                meets_cond = cond(child)
                if dont_include_children_if_parent_is_filtered_out and not meets_cond:
                    continue
                elif not meets_cond and len([c for c in child.children() if isinstance(c, FolderItem)]) == 0:
                    continue
                child_folder = child.folder_filter(cond, include_files=include_files, dont_include_children_if_parent_is_filtered_out=False)
                if len([c for c in child_folder.children() if isinstance(c, FolderItem)]) > 0 or meets_cond:
                    root.add_child(child_folder)
        return root

    def filter_folders_only(self):
        return self.folder_filter(lambda _ : True, include_files=False)

    def filter_out_empty_folders(self):
        root = self.create_root()
        # TODO: maybe we can make this non-recursive?
        for child in self.children():
            if isinstance(child, FileItem):
                root.add_child(FileItem(child.name()))
            if isinstance(child, FolderItem):
                if len(child.children()) == 0:
                    continue
                child_folder = child.filter_out_empty_folders()
                if len(child_folder.children()) > 0:
                    root.add_child(child_folder)
        return root
    
    def file_filter(self, f: Callable[[FileItem], bool], *, filter_empty_folders=True):
        """
            Filters files based on criteria.

            ORDERING NOT GUARANTEED
        """
        root = self.create_root()

        queue = Deque([FilterFolder(self, root)])
        while queue:
            folder = queue.popleft()

            for child in folder.orig.children():
                if isinstance(child, FileItem) and f(child):
                    folder.filtered.add_child(FileItem(child.name()))
                if isinstance(child, FolderItem):
                    child_folder = FolderItem(child.name())
                    folder.filtered.add_child(child_folder)
                    queue.append(FilterFolder(child, child_folder))
        #print(root)
        if filter_empty_folders:
            root = root.filter_out_empty_folders()

        return root

    def sorted(self, key: Callable[[Item], Any], reverse=False):
        root = self.create_root()

        queue = Deque([FilterFolder(self, root)])
        while queue:
            folder = queue.popleft()

            for child in sorted(folder.orig.children(), key=key, reverse=reverse):
                if isinstance(child, FileItem):
                    folder.filtered.add_child(FileItem(child.name()))
                if isinstance(child, FolderItem):
                    child_folder = FolderItem(child.name())
                    folder.filtered.add_child(child_folder)
                    queue.append(FilterFolder(child, child_folder))
        return root


    def create_root(self):
        return FolderItem(self.name())

    def walk(self, fn: Callable[[Item]], file_fn: Optional[Callable[[FileItem]]]=None):
        """
            Apply function to self, then for each children, if it's a file, apply function to file, if it's a folder, call this function on that folder

            if file_fn is supplied, fn is called on folders, file_fn is called on files
        """
        stack: List[FolderItem] = [self]

        while stack:
            item = stack.pop()
            fn(item)
            for child in reversed(item.children()):
                if isinstance(child, FileItem):
                    (file_fn or fn)(child)
                elif isinstance(child, FolderItem):
                    stack.append(child)


 