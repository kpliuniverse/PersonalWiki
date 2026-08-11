import logging
import pathlib
from typing import List

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal

from src.exceptions import GUIException
from src.ui.components.dir_preview import DirPreview
from src.utils.move_info import MoveInfo

class ItemMoveDialog(QDialog):

    items_moved: pyqtSignal = pyqtSignal(MoveInfo)

    def __init__ (self, parent: QWidget, items: List[pathlib.Path], wiki_proper_directory: pathlib.Path):
        super().__init__(parent=parent)

        if not items:
            raise GUIException("ItemMoveDialog created without specifying items to move.")

        self.__items = items
        layout = QVBoxLayout()
        self.setLayout(layout)
        label_text = f"Moving {len(items)} items" if len(items) > 1 else f"Moving {(items[0]).as_posix()}"
        label = QLabel(parent=self, text=label_text)
        layout.addWidget(label)

        self.__dir_preview = DirPreview(self, wiki_proper_directory)
        self.__dir_preview.file_selected.connect(self.__validate_buttons)
        layout.addWidget(self.__dir_preview)

        self.__wiki_directory = wiki_proper_directory

        self.__button_box = QDialogButtonBox(Qt.Orientation.Horizontal, self)
        self.__move_btn = QPushButton(parent=self.__button_box, text="Move")
        self.__button_box.addButton(self.__move_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = QPushButton(parent=self.__button_box, text="Cancel")
        self.__button_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)
        
        self.__button_box.accepted.connect(self.accept)
        self.__button_box.rejected.connect(self.reject)
        layout.addWidget(self.__button_box)
        self.__validate_buttons()

        self.accepted.connect(self.__on_accept)

        
    def __validate_buttons(self):
        self.__move_btn.setDisabled(self.__dir_preview.get_chosen_dir() is None)

    def on_file_select(self):
        self.__validate_buttons()
    
    def __on_accept(self):
        chosen_dir = self.__dir_preview.get_chosen_dir()
        if chosen_dir is None:
            logging.warning("No directory selected, ignoring move request.")
            return
        chosen_dir = self.__wiki_directory / chosen_dir
        self.items_moved.emit(MoveInfo.gen_move_info([self.__wiki_directory / item for item in self.__items], chosen_dir).relative_to(self.__wiki_directory))