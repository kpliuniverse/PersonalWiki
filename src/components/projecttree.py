from collections import deque
from dataclasses import dataclass
from enum import Enum
import logging
import os
import pathlib
import shutil
from typing import Deque, Dict, Optional

from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QMenu,
    QTreeView, 
    QWidget, 
    QVBoxLayout, 
    QToolBar, 
    QHBoxLayout,
    QPushButton
)

from src.components.dialogs.itemnamedialog import ItemNameDialog
from src.exceptions import GUIException
from src.itemmodels.projectitem import ProjectItem
from src.items.items import ItemCreationResult, ItemType

class TreeType(Enum):
    DIR = 0
    FULL = 1
@dataclass(frozen=True)
class ProjectTreeArgs:
    tree_type: TreeType

class ProjectTree(QWidget):
    __tree: QTreeView
    __root_layout = QVBoxLayout()
    __cur_selected_item: Optional[pathlib.Path] = None
    __working_directory: Optional[pathlib.Path] = None

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setLayout(self.__root_layout)
        self.__add_edit_buttons()
        self.__tree = QTreeView(self)
        self.__root_layout.addWidget(self.__tree)
        self.__tree.clicked.connect(self.__on_select)
        self.file_clicked = self.__tree.clicked
        self.file_double_clicked = self.__tree.doubleClicked

        self.__tree.setHeaderHidden(True)


    def __new_menu(self):
        new_menu = QMenu()
        new_menu.addAction("File", lambda: self.__on_new_item(ItemType["PWE"]))
        new_menu.addAction("Folder", lambda: self.__on_new_item(ItemType["FOLDER"]))
        return new_menu

    def __add_edit_buttons(self):
        toolbar = QToolBar(self)
        new_btn = QPushButton(parent=toolbar, text="New")
        new_btn.setMenu(self.__new_menu())
        toolbar.addWidget(new_btn)
        del_btn = QPushButton(parent=toolbar, text="Delete")
        del_btn.clicked.connect(self.__delete_item)
        toolbar.addWidget(del_btn)
        self.__root_layout.addWidget(toolbar)

    def __on_select(self, val: QModelIndex):
        self.__cur_selected_item = pathlib.Path(val.data(Qt.ItemDataRole.UserRole + 1))

    def __create_new_item(self, item: ItemCreationResult):
        if item.typ == ItemType["FOLDER"]:
            item.path.mkdir()
        else:
            with open(item.path, "x") as _:
                pass

        if self.__working_directory:
            self.reload(self.__working_directory)

    def __delete_item(self):
        if not self.__cur_selected_item:
            return
        if self.__cur_selected_item.is_dir():
            shutil.rmtree(self.__cur_selected_item)
            #os.rmdir(self.__cur_selected_item)
        if self.__cur_selected_item.is_file():
            os.remove(self.__cur_selected_item)
        if self.__working_directory:
            self.reload(self.__working_directory)
    
    def __on_new_item(self, item_type: ItemType):
        if self.__working_directory is None:
            raise GUIException("on_new_item() called without working directory")

        if not self.__cur_selected_item:
            dir_to_create = self.__working_directory
        elif self.__cur_selected_item.is_dir():
            dir_to_create = self.__cur_selected_item
        else:
            dir_to_create = self.__cur_selected_item.parent

        dialog = ItemNameDialog(self, item_type, dir_to_create)
        dialog.on_path_selected.connect(self.__create_new_item)
        dialog.exec()
        
    def reload(self, path: pathlib.Path):
        self.__working_directory = path
        item_system_model = QStandardItemModel()
        root_node = item_system_model.invisibleRootItem()
        if root_node is None:
            raise GUIException("Failed fetching root node")
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