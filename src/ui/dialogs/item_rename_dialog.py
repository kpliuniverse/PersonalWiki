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
from src.itemmodels.project_item import ItemInfo
from src.items.items import ItemRecognizedType, ItemCreationResult
from src.utils.item_validity import is_valid_item_name
from src.utils.path_utils import gen_path_string
from src.wiki.wiki import Wiki

@define(frozen=True)
class RenameInfo:
    item: ItemInfo
    new_name: str

    def full_new_path(self) -> pathlib.Path:
        return self.item.path.with_name(self.new_name)

class ItemRenameDialog(QDialog):

    on_name_selected: pyqtSignal = pyqtSignal(RenameInfo)

    
    def __init__(self, parent: QWidget,  item: ItemInfo, wiki: Wiki) -> None:
        
        self.__working_item: ItemInfo = item

        super().__init__(parent)
        self.setWindowTitle("Rename Item")
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setFixedSize(400, 200)
        label = QLabel(parent=self, text="Enter your item/folder name")
        layout.addWidget(label)

        self.__line_edit = QLineEdit(self)
        self.__line_edit.setText(item.path.with_suffix("").name)
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
        
        self.__wiki: Wiki = wiki

        # Width of self.__location_label is inaccurate when retrieved in __init__, it must be running on the app for it to be accurate
        QTimer.singleShot(10, Qt.TimerType.PreciseTimer, self.__update_item_label)
        self.__validate()
        
    def __update_item_label(self) -> None:
        location_text: str = f"at {self.__working_item}"
        metrics = QFontMetrics(self.__location_label.font())
        elided_text: str = metrics.elidedText(location_text, Qt.TextElideMode.ElideMiddle, self.__location_label.width())
        self.__location_label.setText(elided_text)

    def __on_accept(self) -> None:
        self.on_name_selected.emit(RenameInfo(
                item=self.__working_item,
                new_name=self.gen_resultant_path().name
            )
        )

    def gen_resultant_path(self) -> pathlib.Path:
        line_edit_txt: str = self.__line_edit.text()
        txt_stripped: str = line_edit_txt.strip()
        ending: str = self.__working_item.path.suffix
        return self.__working_item.path.with_name(f"{txt_stripped}{ending}")

    def __validate(self) -> None:
        valid = True
        error_msg: str = ""
        line_edit_txt: str = self.__line_edit.text()
        if not is_valid_item_name(line_edit_txt):
            valid = False
            error_msg = "Not a valid item name."
        cur_path: pathlib.Path = self.gen_resultant_path()
        if self.__wiki.exists(cur_path):
            valid = False
            error_msg: str = f"Item/folder {cur_path.as_posix()} already exists"

        self.__error_label.setText(error_msg)
        self.__button.setDisabled(not valid)
        
            