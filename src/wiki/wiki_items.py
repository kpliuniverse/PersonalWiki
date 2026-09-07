from enum import IntEnum, auto, StrEnum
from typing import Union, Optional

import attrs
from returns.result import Result, Failure, Success


class WikiErrorType(StrEnum):
    DuplicateFileName = auto()

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

    def add_child(self, child: UnnamedItem) -> Result[None, WikiErrorType]:
        if child in self.__children:
            return Failure(WikiErrorType.DuplicateFileName)

        self.__children.add(child)
        return Success(None)

    def print(self, __prefix: str = ""):
        """
        Print the item
        Do not use the prefix argument, it's for internal purposes
        """
        # TODO: make this non-recursive
        slash = "" if __prefix == "" else "/"
        print(f"{__prefix}{slash}{self.__name}")
        for child in self.__children:
            if isinstance(child, FileItem):
                print(f"{self.__name}/{child.name()}")
            if isinstance(child, UnnamedFolderItem):
                child.print(f"{self.__name}")


class NamedFolderItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self.__item_type = ItemType.FOLDER
        self.__children: dict[str, NamedItem] = dict()

    def add_child(self, child: NamedItem) -> Result[None, WikiErrorType]:
        if child in self.__children:
            return Failure(WikiErrorType.DuplicateFileName)

        self.__children[child.name()] = child
        return Success(None)

    def print(self, __prefix: str = ""):
        """
        Print the item
        Do not use the prefix argument, it's for internal purposes
        """
        # TODO: make this non-recursive
        slash = "" if __prefix == "" else "/"
        print(f"{__prefix}{slash}{self.name()}")
        for child in self.__children:
            if isinstance(child, FileItem):
                print(f"{self.name()}/{child.name()}")
            if isinstance(child, UnnamedFolderItem):
                child.print(f"{self.name()}")

    def get(self, name: str) -> Optional[NamedItem]:
        return self.__children.get(name, None)