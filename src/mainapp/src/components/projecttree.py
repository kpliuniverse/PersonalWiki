from collections import deque
import pathlib
from typing import Deque, Dict
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QTreeView, QWidget

from src.itemmodels.projectitem import ProjectItem

class ProjectTree(QTreeView):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

    def reload(self, path):
        item_system_model = QStandardItemModel()
        root_node = item_system_model.invisibleRootItem()
        if root_node is None:
            raise Exception("Failed fetching root node")
        dir_to_item: Dict[str, QStandardItem] = dict()
    
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

            self.setModel(item_system_model)
