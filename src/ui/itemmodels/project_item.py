import pathlib
from typing import Optional, override

from PyQt6.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt6.QtCore import Qt
import attrs

from src.consts import ITEM_DATA_ROLE
from src.resources import ResourceManager, ResourceType
from src.wiki.wiki_items import ItemType



@attrs.define
class ItemInfo:
    path: pathlib.Path
    item_type: ItemType
    
class ProjectItem(QStandardItem):
    def __init__(self, info: ItemInfo, name: Optional[str] = None):
        super().__init__()
        self.setEditable(False)
        if name is None:
            self.setText(info.path.name)
        else:
            self.setText(name)
        self.setData(info, ITEM_DATA_ROLE)
        icon = ResourceManager().get(f"icons/48px/{'folder' if info.item_type == ItemType.FOLDER else 'file'}.png")
        assert icon.type == ResourceType.ICON
        self.setIcon(icon.res)
        self.info = info