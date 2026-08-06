from dataclasses import dataclass
import logging
import os
import pathlib
import shutil
from typing import List, Optional

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics

from src.components.dialogs.projectdialog import ProjectDialog, ProjectDialogArgs
from src.exceptions import GUIException
from src.utils.pathutils import gen_path_string


@dataclass(frozen=True)
class MoveInfo:
    paths_deleted: List[pathlib.Path]
    paths_created: List[pathlib.Path]
    src_items: List[pathlib.Path]
    dest: pathlib.Path
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
        location_text = f"at {gen_path_string(self.__chosen_path, self.__wiki_directory)}"
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
            add_root_as_folder=True
        ))
        dialog.on_file_selected.connect(self.__on_chosen)
        dialog.exec()
        
class ItemMoveDialog(QDialog):

    items_moved: pyqtSignal = pyqtSignal(MoveInfo)

    def __init__ (self, parent: QWidget, items: List[pathlib.Path], wiki_directory: pathlib.Path):
        super().__init__(parent=parent)
        for i, item in enumerate(items):
            if not item.is_relative_to(wiki_directory):
                raise GUIException(f"item {item} (index #{i}) is not related to wiki_directory {wiki_directory}")

        if not items:
            raise GUIException("ItemMoveDialog created without specifying items to move.")

        self.__items = items
        layout = QVBoxLayout()
        self.setLayout(layout)
        label_text = f"Moving {len(items)} items" if len(items) > 1 else f"Moving {(items[0].relative_to(wiki_directory)).as_posix()}"
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

        paths_created: List[pathlib.Path] = []
        paths_removed: List[pathlib.Path] = []

        for item in self.__items:
            if (p := item.parent) == chosen_dir:
                logging.warning("File %s is already contained in directory %s, skipping...", p, chosen_dir)
                continue
            
            if item.is_dir():
                for (root,_,files) in os.walk(item, topdown=False):
                    pl_root = pathlib.Path(root)
                    paths_removed.extend((pl_root / f for f in files))
                    paths_removed.append(pl_root)

                for (root,_,files) in os.walk(item, topdown=True):       
                    pl_root = pathlib.Path(root)       
                    paths_created.append(chosen_dir / pl_root.relative_to(item.parent))
                    paths_created.extend((chosen_dir / pl_root.relative_to(item.parent) / f for f in files ))
            if item.is_file():
                paths_removed.append(item)
                paths_created.append(chosen_dir / item.name)

        self.items_moved.emit(MoveInfo(
            paths_created=paths_created,
            paths_deleted=paths_removed,
            src_items=self.__items,
            dest=chosen_dir
        ))