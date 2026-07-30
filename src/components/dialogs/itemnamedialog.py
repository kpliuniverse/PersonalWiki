from dataclasses import dataclass
import pathlib
from typing import Callable, override

from PyQt6 import QtCore
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtCore import Qt, pyqtSignal

from src.items.items import ItemType, ItemCreationResult
from src.utils.filevalidity import valid_wiki_name

class ItemNameDialog(QDialog):

    on_path_selected: pyqtSignal = pyqtSignal(ItemCreationResult)

    
    def __init__(self, parent: QWidget, item_type: ItemType, directory: pathlib.Path):
        self.__working_directory = directory

        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setFixedSize(400, 200)
        label = QLabel(parent=self, text=f"Enter your item/folder name")
        layout.addWidget(label)

        self.__line_edit = QLineEdit(self)
        self.__line_edit.textChanged.connect
        layout.addWidget(self.__line_edit)

        self.__location_label = QLabel(parent=self, text="")
        layout.addWidget(self.__location_label)
        #self.__location_label.setStyleSheet("QLabel {border: 5px solid}")
        location_text = f"at {directory.as_posix()}"
        metrics = QFontMetrics(self.__location_label.font())
        elided_text = metrics.elidedText(location_text, Qt.TextElideMode.ElideMiddle, self.__location_label.width() + 128)
        self.__location_label.setText(elided_text)

        self.__error_label = QLabel(parent=self, text="")
        layout.addWidget(self.__error_label)
        
        self.__button = QPushButton(parent=self, text="Create")
        layout.addWidget(self.__button)
        self.__button.clicked.connect(self.accept)

        self.accepted.connect(self.on_accept)

        self.__item_type = item_type

    def on_accept(self):
        self.on_path_selected.emit(ItemCreationResult(
                path=self.gen_resultatnt_path(),
                typ=self.__item_type
            )
        )

    def gen_resultatnt_path(self):
        line_edit_txt = self.__line_edit.text()
        txt_stripped = line_edit_txt.strip()
        ending = ""
        if self.__item_type == ItemType["PWE"]:
            ending = ".pwe"
        return self.__working_directory / f"{txt_stripped}{ending}"

    def __validate(self):
        valid = True
        error_msg = ""
        line_edit_txt = self.__line_edit.text()
        if not valid_wiki_name(line_edit_txt):
            valid = False
            error_msg = "Not a valid item name."

        if self.gen_resultatnt_path().exists():
            valid = False
            error_msg = f"Item/folder already exists"

        self.__error_label.setText(error_msg)
        self.__button.setDisabled(not valid)
        
            