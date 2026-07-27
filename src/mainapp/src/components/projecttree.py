from collections import deque
from dataclasses import dataclass
from enum import Enum
import logging
import pathlib
from typing import Deque, Dict
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QTreeView, 
    QWidget, 
    QVBoxLayout, 
    QToolBar, 
    QHBoxLayout,
    QPushButton
)

from src.itemmodels.projectitem import ProjectItem

class TreeType(Enum):
    DIR = 0
    FULL = 1
@dataclass(frozen=True)
class ProjectTreeArgs:
    tree_type: TreeType
    
class ProjectTree(QWidget):
    __tree: QTreeView
    __root_layout = QVBoxLayout()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setLayout(self.__root_layout)
        self.add_edit_buttons()
        self.__tree = QTreeView(self)
        self.__root_layout.addWidget(self.__tree)
        self.file_clicked = self.__tree.clicked
        self.file_double_clicked = self.__tree.doubleClicked
        self.__tree.setHeaderHidden(True)
        
    def add_edit_buttons(self):
        toolbar = QToolBar(self)
        new_btn = QPushButton(parent=toolbar, text="New")
        toolbar.addWidget(new_btn)
        del_btn = QPushButton(parent=toolbar, text="Delete")
        toolbar.addWidget(del_btn)
        self.__root_layout.addWidget(toolbar)

    def reload(self, path: pathlib.Path):
        item_system_model = QStandardItemModel()
        root_node = item_system_model.invisibleRootItem()
        if root_node is None:
            logging.error("Failed fetching root node")
            return
        root_node.setText("Aaargh")
        dir_to_item: Dict[str, QStandardItem] = dict()
        item_system_model.setHorizontalHeaderLabels([])
        subdirs: Deque[pathlib.Path] = deque([path])
        dir_to_item[path.as_posix()] = root_node
        while (len(subdirs) > 0):
            subdir = subdirs.popleft()
            for path in subdir.iterdir():
                if path.is_junction() and path.is_symlink():
                    continue
                project_item = ProjectItem(path)

                if path.is_dir():
                    subdirs.append(path)
                    dir_to_item[path.as_posix()] = project_item
                    dir_to_item[subdir.as_posix()].appendRow(project_item)

                if path.is_file():
                    dir_to_item[subdir.as_posix()].appendRow(project_item)

            self.__tree.setModel(item_system_model)       