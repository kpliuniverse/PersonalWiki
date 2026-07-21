import pathlib
from typing import override

from PyQt6.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt6.QtCore import Qt
class ProjectItem(QStandardItem):
    def __init__(self, path: pathlib.Path):
        super().__init__()
        self.setEditable(False)
        self.setText(path.name)
        self.setData(path, Qt.ItemDataRole.UserRole + 1)
    