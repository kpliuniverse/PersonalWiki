import pathlib
from typing import List, Optional

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFontMetrics

from src.components.dialogs.projectdialog import ProjectDialog, ProjectDialogArgs
from src.exceptions import GUIException
from src.utils.pathutils import gen_path_string


class DirPreview(QWidget):
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

    def get_chosen_file(self):
        return self.__chosen_path
    
    def __on_browse(self):
        ProjectDialog(self, self.__wiki_directory, ProjectDialogArgs(
            dir_only=True
        )).exec()

        
class ItemMoveDialog(QDialog):

    def __init__ (self, parent: QWidget, items: List[pathlib.Path], wiki_directory: pathlib.Path):
        super().__init__(parent=parent)
        for i, item in enumerate(items):
            if not item.is_relative_to(wiki_directory):
                raise GUIException(f"item {item} (index #{i}) is not related to wiki_directory {wiki_directory}")

        if not items:
            raise GUIException("ItemMoveDialog created without specifying items to move.")

        layout = QVBoxLayout()
        self.setLayout(layout)
        label_text = f"Moving {len(items)} items" if len(items) > 1 else f"Moving {(items[0].relative_to(wiki_directory)).as_posix()}"
        label = QLabel(parent=self, text=label_text)
        layout.addWidget(label)

        dir_preview = DirPreview(self, wiki_directory)
        layout.addWidget(dir_preview)

        self.__wiki_directory = wiki_directory

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, Qt.Orientation.Horizontal, self)
        button_box.rejected.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
