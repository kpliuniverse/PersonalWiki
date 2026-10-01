import pathlib
from typing import Optional, override

from PyQt6.QtGui import QFont, QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtCore import Qt
import attrs

from src.consts import ITEM_DATA_ROLE
from src.resources import ResourceManager, ResourceType
from src.ui.utils.get_file_icon import get_icon_from_extension
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
        # Load icons lazily to avoid constructing QIcon/QPixmap before a QGuiApplication exists
        if info.item_type == ItemType.FOLDER:
            icon = ResourceManager().assert_get_res("icons/48px/folder.png", assert_type=QIcon)
        else:
            icon = get_icon_from_extension(info.path.suffix)
        self.setIcon(icon)
        self.info = info