import pathlib
from typing import List

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.exceptions import GUIException

class ItemMoveDialog(QDialog):

    def __init__ (self, parent: QWidget, items: List[pathlib.Path], wiki_directory: pathlib.Path):

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


    def __dir_chooser(self):
        dir_chooser = QWidget()
        dir_chooser_layout = QHBoxLayout()
        dir_chooser.setLayout(dir_chooser_layout)

        location_text = "at "
        return dir_chooser