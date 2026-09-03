from enum import IntEnum

import attrs

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

class FileItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self.__item_type = ItemType.FILE

class FolderItem(Item):
    def __init__(self, name: str):
        super().__init__(name)
        self.__item_type = ItemType.FOLDER
        self.__children: list[Item] = []

    def children(self):
        return self.__children



