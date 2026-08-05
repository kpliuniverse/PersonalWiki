from dataclasses import dataclass
from enum import Enum
import pathlib

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from src.components.projecttree import ProjectTree, ProjectTreeArgs

@dataclass
class ProjectDialogArgs:
    dir_only: bool

class ProjectDialog(QDialog):

    def __init__(self, parent: QWidget, wiki_dir: pathlib.Path, args: ProjectDialogArgs):
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.__tree = ProjectTree(self, ProjectTreeArgs(
            dir_only=args.dir_only
        ))
        self.__tree.load(wiki_dir)
        layout.addWidget(self.__tree)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, Qt.Orientation.Vertical, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    