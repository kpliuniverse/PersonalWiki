from enum import Enum
import pathlib
from typing import Optional

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from attrs import define

from src.ui.components.project_tree import ProjectTree, ProjectTreeArgs

@define
class ProjectDialogArgs:
    dir_only: bool = False
    add_root_as_folder: bool = False

class ProjectDialog(QDialog):

    on_file_selected: pyqtSignal = pyqtSignal(pathlib.Path)

    def __init__(self, parent: QWidget, wiki_dir: pathlib.Path, args: ProjectDialogArgs):
        self.__cur_file_selected: Optional[pathlib.Path] = None
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.__tree = ProjectTree(self, ProjectTreeArgs(
            dir_only=args.dir_only,
            add_root_as_folder=args.add_root_as_folder,
            read_only=True
        ))
        self.__tree.load(wiki_dir)
        self.__tree.item_clicked.connect(self.__on_tree_select)
        layout.addWidget(self.__tree)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, Qt.Orientation.Vertical, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.accepted.connect(self.__on_accepted)

    def __on_accepted(self):
        if self.__cur_file_selected is not None:
            self.on_file_selected.emit(self.__cur_file_selected)

    def __on_tree_select(self):
        self.__cur_file_selected = self.__tree.get_cur_selected_path()
        
