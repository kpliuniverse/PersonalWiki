from dataclasses import dataclass
import logging
import pathlib
from typing import Callable, override

from PyQt6 import QtCore
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from attrs import define


from src.exceptions import GUIException
from src.items.items import ItemType, ItemCreationResult
from src.utils.item_validity import valid_item_name
from src.utils.path_utils import gen_path_string


@define(frozen=True)
class RenameInfo:
    file: pathlib.Path
    new_name: str

    def full_new_name(self):
        return self.file.with_name(self.new_name)

class ItemRenameDialog(QDialog):

    on_name_selected: pyqtSignal = pyqtSignal(RenameInfo)

    
    def __init__(self, parent: QWidget,  item: pathlib.Path, wiki_proper_directory: pathlib.Path):
        
        self.__working_item = item

        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setFixedSize(400, 200)
        label = QLabel(parent=self, text="Enter your item/folder name")
        layout.addWidget(label)

        self.__line_edit = QLineEdit(self)
        self.__line_edit.setText(item.with_suffix("").name)
        self.__line_edit.textChanged.connect(self.__validate)
        layout.addWidget(self.__line_edit)

        self.__location_label = QLabel(parent=self, text="")
        layout.addWidget(self.__location_label)
        #self.__location_label.setStyleSheet("QLabel {border: 5px solid}")

        self.__error_label = QLabel(parent=self, text="")
        layout.addWidget(self.__error_label)
        
        self.__button = QPushButton(parent=self, text="Create")
        layout.addWidget(self.__button)
        self.__button.clicked.connect(self.accept)

        self.accepted.connect(self.__on_accept)
        
        self.__wiki_directory = wiki_proper_directory

        # Width of self.__location_label is inaccurate when retrieved in __init__, it must be running on the app for it to be accurate
        QTimer.singleShot(10, Qt.TimerType.PreciseTimer, self.__update_item_label)
        self.__validate()
        
    def __update_item_label(self):
        location_text = f"at {self.__working_item}"
        metrics = QFontMetrics(self.__location_label.font())
        elided_text = metrics.elidedText(location_text, Qt.TextElideMode.ElideMiddle, self.__location_label.width())
        self.__location_label.setText(elided_text)

    def __on_accept(self):
        self.on_name_selected.emit(RenameInfo(
                file=self.__working_item,
                new_name=self.gen_resultatnt_path().name
            )
        )

    def gen_resultatnt_path(self):
        line_edit_txt = self.__line_edit.text()
        txt_stripped = line_edit_txt.strip()
        ending = self.__working_item.suffix
        return self.__working_item.with_name(f"{txt_stripped}{ending}")

    def __validate(self):
        valid = True
        error_msg = ""
        line_edit_txt = self.__line_edit.text()
        if not valid_item_name(line_edit_txt):
            valid = False
            error_msg = "Not a valid item name."
        cur_path = self.__wiki_directory / self.gen_resultatnt_path()
        if cur_path.exists():
            valid = False
            error_msg = f"Item/folder already exists"

        self.__error_label.setText(error_msg)
        self.__button.setDisabled(not valid)
        
            