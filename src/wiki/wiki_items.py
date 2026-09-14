import logging
import pathlib
from enum import IntEnum, auto, StrEnum
from typing import Any, Deque, List, Protocol, Union, Optional, Callable

import attrs
from returns.result import Result, Failure, Success


class WikiError(StrEnum):
    DUPLICATE_FILE_NAME = auto()
    ITEM_NOT_FOUND = auto()
    NOT_A_FOLDER_ITEM = auto()

class ItemType(IntEnum):
    FILE = 0
    FOLDER = 1


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

UnnamedItem = Union["FileItem", "UnnamedFolderItem"]
NamedItem = Union["FileItem", "NamedFolderItem"]

class FileItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self._item_type = ItemType.FILE

@attrs.define
class FilterFolder:
    orig: UnnamedFolderItem
    filtered: UnnamedFolderItem

def sort_alphabetically_key(n: UnnamedItem):
    return n.name()


class UnnamedFolderItem(Item):
    """
        An item that contains child items that are stored in a list.
    """
    def __init__(self, name: str):
        super().__init__(name)
        self._item_type = ItemType.FOLDER
        self.__children: List[UnnamedItem] = []

    def add_child(self, child: UnnamedItem) -> Result[None, WikiError]:
        if child in self.__children:
            return Failure(WikiError.DUPLICATE_FILE_NAME)

        self.__children.append(child)
        return Success(None)

    def to_str_list(self, __prefix: str = ""):
        """
            Converts to str list.
            Is used for testing
        """
        """
        Print the item
        Do not use the prefix argument, it's for internal purposes
        """
        # TODO: make this non-recursive
        slash = "" if __prefix == "" else "/"
        disp = f"{__prefix}{slash}{self.name()}"
        out: List[str] = [disp]
        for child in self.__children:
            if isinstance(child, FileItem):
                out.append(f"{disp}/{child.name()}")
            if isinstance(child, UnnamedFolderItem):
                out.extend(child.to_str_list(disp))
        return out
    
    def __str__(self):
        return "\n".join(self.to_str_list())
        
        
    def children(self) -> List[UnnamedItem]:
        return self.__children

    def folder_filter(self, cond: Callable[[UnnamedFolderItem], bool], *, include_files, dont_include_children_if_parent_is_filtered_out=False):
        """
            Filters folders based on criteria.

            `include_files` determine if files should be included
        """
        root = self.create_root()

        for child in self.children():
            if isinstance(child, FileItem) and include_files:
                root.add_child(FileItem(child.name()))
            if isinstance(child, UnnamedFolderItem):
                meets_cond = cond(child)
                if dont_include_children_if_parent_is_filtered_out and not meets_cond:
                    continue
                elif not meets_cond and len([c for c in child.children() if isinstance(c, UnnamedFolderItem)]) == 0:
                    continue
                child_folder = child.folder_filter(cond, include_files=include_files, dont_include_children_if_parent_is_filtered_out=False)
                if len([c for c in child_folder.children() if isinstance(c, UnnamedFolderItem)]) > 0 or meets_cond:
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
            if isinstance(child, UnnamedFolderItem):
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
                if isinstance(child, UnnamedFolderItem):
                    child_folder = UnnamedFolderItem(child.name())
                    folder.filtered.add_child(child_folder)
                    queue.append(FilterFolder(child, child_folder))
        #print(root)
        if filter_empty_folders:
            root = root.filter_out_empty_folders()

        return root

    def sorted(self, key: Callable[[UnnamedItem], Any], reverse=False):
        root = self.create_root()

        queue = Deque([FilterFolder(self, root)])
        while queue:
            folder = queue.popleft()

            for child in sorted(folder.orig.children(), key=key, reverse=reverse):
                if isinstance(child, FileItem):
                    folder.filtered.add_child(FileItem(child.name()))
                if isinstance(child, UnnamedFolderItem):
                    child_folder = UnnamedFolderItem(child.name())
                    folder.filtered.add_child(child_folder)
                    queue.append(FilterFolder(child, child_folder))
        return root


    def create_root(self):
        return UnnamedFolderItem(self.name())

        
class NamedFolderItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self._item_type = ItemType.FOLDER
        self.__children: dict[str, NamedItem] = dict()

    def add_child(self, child: NamedItem) -> Result[None, WikiError]:
        if child in self.__children:
            return Failure(WikiError.DUPLICATE_FILE_NAME)

        self.__children[child.name()] = child
        return Success(None)

    def print(self, __prefix: str = ""):
        """
        Print the item
        Do not use the prefix argument, it's for internal purposes
        """
        # TODO: make this non-recursive
        slash = "" if __prefix == "" else "/"
        name = f"{__prefix}{slash}{self.name()}"
        print(name)
        for child in self.__children.values():
            if isinstance(child, FileItem):
                print(f"{name}/{child.name()}")
            if isinstance(child, NamedFolderItem):
                child.print(f"{name}")

    def get(self, name: str) -> Optional[NamedItem]:
        """
            Get the item by name. Returns None if not found
        """
        return self.__children.get(name, None)

    def get_path(self, path: pathlib.Path) -> Result[NamedItem, WikiError]:
        """
            Get the item by path.
            e.g. `folder.get_path(pathlib.Path("a/b/c"))` is equal to folder.get("a").get("b").get("c")
            If, for example, a and b, is a file, returns `ItemError.NOT_A_FOLDER_ITEM`.
        """
        if len(path.parts) == 0:

            return Success(self)
        cur_folder: NamedFolderItem = self

        for part in path.parts[:-1]:
            item = cur_folder.get(part)
            if item is None:
                return Failure(WikiError.ITEM_NOT_FOUND)
            if isinstance(item, FileItem):
                return Failure(WikiError.NOT_A_FOLDER_ITEM)
            cur_folder = item
        if (final_item := cur_folder.get(path.name)) is None:
            return Failure(WikiError.ITEM_NOT_FOUND)
        return Success(final_item)

    def to_unnamed_folder_item(self) -> UnnamedFolderItem:
        # TODO: make this non-recursive
        root = UnnamedFolderItem(self.name())
        for child in self.__children.values():
            if isinstance(child, FileItem):
                root.add_child(child)
            if isinstance(child, NamedFolderItem):
                root.add_child(child.to_unnamed_folder_item())
        return root