import pathlib
from typing import Optional, override

from PyQt6.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt6.QtCore import Qt
class ProjectItem(QStandardItem):
    def __init__(self, path: pathlib.Path, name: Optional[str] = None):
        super().__init__()
        self.setEditable(False)
        if name is None:
            self.setText(path.name)
        else:
            self.setText(name)
        self.setData(path, Qt.ItemDataRole.UserRole + 1)
    