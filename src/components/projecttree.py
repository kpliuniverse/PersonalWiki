from collections import deque
from dataclasses import dataclass
from enum import Enum
import pathlib
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

from src.exceptions import GUIException
from src.itemmodels.projectitem import ProjectItem


@dataclass(frozen=True)
class ProjectTreeArgs:
    dir_only: bool = False
    add_root_as_folder: bool = False
class ProjectTree(QWidget):
    __tree: QTreeView


    def __init__(self, parent: QWidget, tree_args: ProjectTreeArgs):
        self.__args = tree_args
        self.__root_layout = QVBoxLayout()
        self.__index_dict: Dict[str, QStandardItem] = dict()

        super().__init__(parent=parent)
        self.setLayout(self.__root_layout)
        # self.__add_edit_buttons()
        self.__tree = QTreeView(self)
        self.__root_layout.addWidget(self.__tree)
        self.__tree.clicked.connect(self.__on_select)
        self.item_clicked = self.__tree.clicked
        self.file_double_clicked = self.__tree.doubleClicked
        self.__tree.setHeaderHidden(True)

        self.__cur_selected_item: Optional[QModelIndex] = None
        self.__cur_selected_path: Optional[pathlib.Path] = None
        self.__working_directory: Optional[pathlib.Path] = None

    def __on_select(self, val: QModelIndex):
        self.__cur_selected_item = val
        self.__cur_selected_path = pathlib.Path(self.__cur_selected_item.data(Qt.ItemDataRole.UserRole + 1))

    def get_cur_selected_path(self):    
        return self.__cur_selected_path


    def delete_item(self, path: pathlib.Path):
        """
            Remove a path from the project tree. Note that it doesn't actuall delete the item in filesystem
        """
        if model := self.__tree.model():
            item = self.__index_dict[path.as_posix()]
            index = item.index()

            items: deque[QStandardItem] = deque([item])
        
            while len(items) > 0:
                item = items.popleft()
                cur_path: pathlib.Path = item.data(Qt.ItemDataRole.UserRole + 1)
                self.__index_dict.pop(cur_path.as_posix())
                for row in range(item.rowCount()):
                    if child := item.child(row, 0):
                        items.append(child)
        
            model.removeRow(index.row(), index.parent())

    def get_selected_indexes(self):
        return self.__tree.selectedIndexes()

    def get_working_directory(self):
        return self.__working_directory
    
    def add_path(self, path: pathlib.Path):
        """
            Add a path to the project tree. Note that it doesn't actually create the item in the filesystem.
        """
        project_item = ProjectItem(path)
        try:
            self.__index_dict[path.parent.as_posix()].appendRow(project_item)
            self.__index_dict[path.as_posix()] = project_item
        except KeyError as exc:
            raise GUIException(f"It seems like parent of '{path}' ({path.parent}) doesn't exist") from exc

    def load(self, directory: pathlib.Path):
        """
            Loads the widget with a specific path
        """
        self.__working_directory = directory
        item_system_model = QStandardItemModel()
        root_node = item_system_model.invisibleRootItem()
        if root_node is None:
            raise GUIException("Failed fetching root node")
        dir_to_item: Dict[str, QStandardItem] = dict()
        item_system_model.setHorizontalHeaderLabels([])
        subdirs: Deque[pathlib.Path] = deque([directory])
        dir_to_item[directory.as_posix()] = root_node
        while len(subdirs) > 0:
            subdir = subdirs.popleft()
            for path in subdir.iterdir():
                if path.is_junction() and path.is_symlink():
                    continue
                project_item = ProjectItem(path)
                if path.is_dir():
                    subdirs.append(path)
                    dir_to_item[path.as_posix()] = project_item
                    dir_to_item[subdir.as_posix()].appendRow(project_item)

                if path.is_file() and not self.__args.dir_only:
                    dir_to_item[subdir.as_posix()].appendRow(project_item)

        self.__tree.setModel(item_system_model)

        if self.__args.add_root_as_folder:
            root_node.appendRow(ProjectItem(pathlib.Path(directory), name="(root)"))

        self.__index_dict.clear()
        self.__index_dict[directory.as_posix()] = root_node
        items: deque[QStandardItem] = deque([root_node])
        
        while len(items) > 0:
            item = items.popleft()
            for row in range(item.rowCount()):
                if child := item.child(row, 0):
                    data: pathlib.Path = child.data(Qt.ItemDataRole.UserRole + 1)
                    self.__index_dict[data.as_posix()] = child
                    items.append(child)