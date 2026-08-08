from dataclasses import dataclass
import logging
import os
import pathlib
import shutil
from typing import List, Optional

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics

from src.ui.components.dialogs.project_dialog import ProjectDialog, ProjectDialogArgs
from src.exceptions import GUIException
from src.utils.move_info import MoveInfo
from src.utils.path_utils import gen_path_string



        
class DirPreview(QWidget):

    file_selected: pyqtSignal = pyqtSignal()
    def __init__(self, parent: QWidget, wiki_dir: pathlib.Path):
        super().__init__(parent=parent)

        dir_chooser_layout = QHBoxLayout()
        self.setLayout(dir_chooser_layout)

        self.__location_label = QLabel(parent=self)
        dir_chooser_layout.addWidget(self.__location_label)

        browse_button = QPushButton(parent=self, text="Browse")
        browse_button.clicked.connect(self.__on_browse)
        dir_chooser_layout.addWidget(browse_button)

        QTimer.singleShot(10, lambda: self.__location_label.setText)
        self.__wiki_directory = wiki_dir
        self.__chosen_path: Optional[pathlib.Path] = None
        
        self.__update_label()
        
    def __update_label(self):
        if self.__chosen_path is None:
            self.__location_label.setText("(no chosen path)")
            return
        location_text = f"at {gen_path_string(self.__wiki_directory / self.__chosen_path, self.__wiki_directory)}"
        metrics = QFontMetrics(self.__location_label.font())
        elided_text = metrics.elidedText(location_text, Qt.TextElideMode.ElideMiddle, self.__location_label.width())
        self.__location_label.setText(elided_text)

    def __on_chosen(self, chosen_path: pathlib.Path):
        self.__chosen_path = chosen_path
        self.__update_label()
        self.file_selected.emit()

    def get_chosen_dir(self):
        return self.__chosen_path
    
    def __on_browse(self):
        dialog = ProjectDialog(self, self.__wiki_directory, ProjectDialogArgs(
            dir_only=True,
            add_root_as_folder=True,
            
            
        ))
        dialog.on_file_selected.connect(self.__on_chosen)
        dialog.exec()
        
class ItemMoveDialog(QDialog):

    items_moved: pyqtSignal = pyqtSignal(MoveInfo)

    def __init__ (self, parent: QWidget, items: List[pathlib.Path], wiki_directory: pathlib.Path):
        super().__init__(parent=parent)

        if not items:
            raise GUIException("ItemMoveDialog created without specifying items to move.")

        self.__items = items
        layout = QVBoxLayout()
        self.setLayout(layout)
        label_text = f"Moving {len(items)} items" if len(items) > 1 else f"Moving {(items[0]).as_posix()}"
        label = QLabel(parent=self, text=label_text)
        layout.addWidget(label)

        self.__dir_preview = DirPreview(self, wiki_directory)
        self.__dir_preview.file_selected.connect(self.__validate_buttons)
        layout.addWidget(self.__dir_preview)

        self.__wiki_directory = wiki_directory

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