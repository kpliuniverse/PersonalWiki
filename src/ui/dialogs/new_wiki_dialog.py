import logging
import pathlib
from typing import Optional

from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal


from src.exceptions import GUIException
from src.ui.components.dir_preview import SystemDirPreview
from src.utils.item_validity import valid_item_name

class NewWikiDialog(QDialog):

    on_name_selected: pyqtSignal = pyqtSignal(pathlib.Path)

    
    def __init__(self, parent: QWidget):

        super().__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        label = QLabel(parent=self, text="Enter your wiki name")
        layout.addWidget(label)


        self.__line_edit = QLineEdit(self)
        self.__line_edit.textChanged.connect(self.__validate)
        layout.addWidget(self.__line_edit)

        self.__dir_preview = SystemDirPreview(self)
        self.__dir_preview.file_selected.connect(self.__on_select)
        layout.addWidget(self.__dir_preview)
        
        self.__error_label = QLabel(parent=self, text="")
        layout.addWidget(self.__error_label)
        
        self.__button = QPushButton(parent=self, text="Create")
        layout.addWidget(self.__button)
        self.__button.clicked.connect(self.accept)

        self.accepted.connect(self.__on_accept)
        self.__validate()
        # Width of self.__location_label is inaccurate when retrieved in __init__, it must be running on the app for it to be accurate
        # QTimer.singleShot(10, Qt.TimerType.PreciseTimer, self.__update_item_label)
        
    def __on_accept(self):
        if (p := self.get_resultant_path()) is None:
            raise GUIException("Accepted without selected path.")
        self.on_name_selected.emit(p)

    def __on_select(self):
        self.__validate()

    def get_resultant_path(self) -> Optional[pathlib.Path]:
        """
            Get the resulting path.
        """
        if (d := self.__dir_preview.get_chosen_dir()) is None:
            return None
        out = d / self.__line_edit.text()
        return out

    def __validate(self):
        valid = True
        error_msg = ""
        line_edit_txt = self.__line_edit.text()
        if not valid_item_name(line_edit_txt):
            valid = False
            error_msg = "Not a valid item name."
        elif (p := self.get_resultant_path()) is not None:
            if p.exists():
                valid = False
                error_msg = "Item/folder already exists"
        else:
            valid = False
        self.__error_label.setText(error_msg)
        self.__button.setDisabled(not valid)