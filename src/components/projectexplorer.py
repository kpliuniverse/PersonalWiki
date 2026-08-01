import logging
import os
import pathlib
import shutil

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
from src.components.projecttree import ProjectTree
from src.exceptions import GUIException
from src.items.items import ItemCreationResult, ItemType

class ProjectExplorer(QWidget):
    __project_tree: ProjectTree
    __root_layout = QVBoxLayout()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setLayout(self.__root_layout)
        self.__root_layout.addWidget(self.__edit_toolbar())
        self.__project_tree = ProjectTree(self)
        self.__root_layout.addWidget(self.__project_tree)
        self.file_clicked = self.__project_tree.file_clicked
        self.file_double_clicked = self.__project_tree.file_double_clicked

    def __new_menu(self):
        new_menu = QMenu()
        new_menu.addAction("File", lambda: self.__on_new_item(ItemType["PWE"]))
        new_menu.addAction("Folder", lambda: self.__on_new_item(ItemType["FOLDER"]))
        return new_menu

    def __edit_toolbar(self):
        toolbar = QToolBar(self)
        new_btn = QPushButton(parent=toolbar, text="New")
        new_btn.setMenu(self.__new_menu())
        toolbar.addWidget(new_btn)
        del_btn = QPushButton(parent=toolbar, text="Delete")
        del_btn.clicked.connect(self.__on_delete_item)
        toolbar.addWidget(del_btn)
        return toolbar

    def __create_new_item(self, item: ItemCreationResult):
        if item.typ == ItemType["FOLDER"]:
            item.path.mkdir()
        else:
            with open(item.path, "x", encoding="utf-8") as _:
                pass
        self.__project_tree.add_path(item.path)
        # self.__index_dict[item.path.parent.as_posix()].appendRow(project_item)
        # self.__index_dict[item.path.as_posix()] = project_item

    def __delete_item(self, item: pathlib.Path):
        if item.is_dir():
            shutil.rmtree(item)
            #os.rmdir(self.__cur_selected_item)
        if item.is_file():
            os.remove(item)

    def __on_delete_item(self):

        for index in self.__project_tree.get_selected_indexes():
            selected_item: pathlib.Path = index.data(Qt.ItemDataRole.UserRole + 1)
            if not selected_item or not isinstance(selected_item, pathlib.Path):
                logging.error("Selected item is None or not pathlib.Path type=%s", type(selected_item))
                continue
            self.__delete_item(selected_item)
            self.__project_tree.delete_item(selected_item)
            
    def __on_new_item(self, item_type: ItemType):
        workdir = self.__project_tree.get_working_directory()

        if workdir is None:
            raise GUIException("on_new_item() called without working directory")
        selected_path = self.__project_tree.get_cur_selected_path()
        if not selected_path:
            dir_to_create = workdir
        elif selected_path.is_dir():
            dir_to_create = selected_path
        else:
            dir_to_create = selected_path.parent

        dialog = ItemNameDialog(self, item_type, dir_to_create)
        dialog.on_path_selected.connect(self.__create_new_item)
        dialog.exec()

    def load(self, directory: pathlib.Path):
        """
            Loads the widget with a specific path
        """
        self.__project_tree.load(directory)