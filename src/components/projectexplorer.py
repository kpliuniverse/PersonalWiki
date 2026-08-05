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

from src.components.dialogs.itemmovedialog import ItemMoveDialog, MoveInfo
from src.components.dialogs.itemnamedialog import ItemNameDialog
from src.components.projecttree import ProjectTree, ProjectTreeArgs
from src.exceptions import GUIException
from src.items.items import ItemCreationResult, ItemType


class ToolBar(QToolBar):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.new_btn = QPushButton(parent=self, text="New")
        self.addWidget(self.new_btn)

        self.move_btn = QPushButton(parent=self, text="Move")
        self.addWidget(self.move_btn)

        self.del_btn = QPushButton(parent=self, text="Delete")
        self.addWidget(self.del_btn)
class ProjectExplorer(QWidget):

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.__root_layout = QVBoxLayout()
        self.setLayout(self.__root_layout)
        self.__toolbar = self.__edit_toolbar()
        self.__root_layout.addWidget(self.__toolbar)
        self.__project_tree = ProjectTree(self, ProjectTreeArgs(
            dir_only=False
        ))
        self.__root_layout.addWidget(self.__project_tree)

        self.__project_tree.item_clicked.connect(self.__validate_btns)
        self.file_clicked = self.__project_tree.item_clicked
        self.file_double_clicked = self.__project_tree.file_double_clicked
        self.__validate_btns()

    def __validate_btns(self):
        has_selection = len(self.__project_tree.get_selected_indexes()) > 0
        self.__toolbar.move_btn.setDisabled(not has_selection)
        self.__toolbar.del_btn.setDisabled(not has_selection)

    def __new_menu(self):
        new_menu = QMenu()
        new_menu.addAction("File", lambda: self.__on_new_item(ItemType["PWE"]))
        new_menu.addAction("Folder", lambda: self.__on_new_item(ItemType["FOLDER"]))
        return new_menu

    def __get_workdir(self):
        workdir = self.__project_tree.get_working_directory()

        if workdir is None:
            raise GUIException("on_new_item() called without working directory")

        return workdir


    def __update(self, move_info: MoveInfo):
        for path in move_info.paths_created:
            self.__project_tree.add_path(path)

        for path2 in move_info.paths_deleted:
            self.__project_tree.delete_item(path2)

    def __on_move_item(self):
        workdir = self.__get_workdir()

        selected_items = []
        for index in self.__project_tree.get_selected_indexes():
            selected_item: pathlib.Path = index.data(Qt.ItemDataRole.UserRole + 1)
            if not selected_item or not isinstance(selected_item, pathlib.Path):
                logging.error("Selected item is None or not pathlib.Path type=%s", type(selected_item))
                continue
            selected_items.append(selected_item)

        dialog = ItemMoveDialog(self, selected_items, workdir)
        dialog.items_moved.connect(self.__update)
        dialog.exec()

    def __edit_toolbar(self):
        toolbar = ToolBar(self)

        toolbar.new_btn.setMenu(self.__new_menu())
        toolbar.del_btn.clicked.connect(self.__on_delete_item)
        toolbar.move_btn.clicked.connect(self.__on_move_item)

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
        workdir = self.__get_workdir()
        selected_path = self.__project_tree.get_cur_selected_path()
        if not selected_path:
            dir_to_create = workdir
        elif selected_path.is_dir():
            dir_to_create = selected_path
        else:
            dir_to_create = selected_path.parent

        dialog = ItemNameDialog(self, item_type, dir_to_create, workdir)
        dialog.on_path_selected.connect(self.__create_new_item)
        dialog.exec()

    def load(self, directory: pathlib.Path):
        """
            Loads the widget with a specific path
        """
        self.__project_tree.load(directory)

    def refresh(self):
        self.__project_tree.load(self.__get_workdir())