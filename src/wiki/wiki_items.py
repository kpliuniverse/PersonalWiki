import pathlib
from enum import IntEnum, auto, StrEnum
from typing import Union, Optional

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
    __item_type: ItemType
    def __init__(self, name: str):
        self.__name = name

    def name(self):
        return self.__name

    def item_type(self):
        return self.__item_type

    def __hash__(self):
        return hash(self.__name)

UnnamedItem = Union["FileItem", "UnnamedFolderItem"]
NamedItem = Union["FileItem", "NamedFolderItem"]

class FileItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self.__item_type = ItemType.FILE


class UnnamedFolderItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self.__item_type = ItemType.FOLDER
        self.__children: set[UnnamedItem] = set()

    def add_child(self, child: UnnamedItem) -> Result[None, WikiError]:
        if child in self.__children:
            return Failure(WikiError.DUPLICATE_FILE_NAME)

        self.__children.add(child)
        return Success(None)

    def print(self, __prefix: str = ""):
        """
        Print the item
        Do not use the prefix argument, it's for internal purposes
        """
        # TODO: make this non-recursive
        slash = "" if __prefix == "" else "/"
        disp = f"{__prefix}{slash}{self.name()}"
        print(disp)
        for child in self.__children:
            if isinstance(child, FileItem):
                print(f"{disp}/{child.name()}")
            if isinstance(child, UnnamedFolderItem):
                child.print(disp)


class NamedFolderItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self.__item_type = ItemType.FOLDER
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

    def get_path(self, path: pathlib.Path) -> Result[NamedItem, ItemError]:
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