import logging
import pathlib

from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtCore import QTimer, Qt, pyqtSignal


from src.exceptions import GUIException
from src.items.items import ItemType, ItemCreationResult
from src.ui.components.dir_preview import ProjectDirPreview
from src.utils.item_validity import valid_item_name

class ItemNameDialog(QDialog):

    on_name_selected: pyqtSignal = pyqtSignal(ItemCreationResult)

    
    def __init__(self, parent: QWidget, item_type: ItemType, directory: pathlib.Path, wiki_proper_directory: pathlib.Path):
        logging.debug("directory=%s, wiki_proper=%s", directory, wiki_proper_directory)

        self.__working_directory = directory

        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setFixedSize(400, 200)
        label = QLabel(parent=self, text="Enter your item/folder name")
        layout.addWidget(label)


        self.__line_edit = QLineEdit(self)
        self.__line_edit.textChanged.connect(self.__validate)
        layout.addWidget(self.__line_edit)

        self.__dir_preview = ProjectDirPreview(self, wiki_proper_directory, pre_chosen_dir=directory)
        self.__dir_preview.file_selected.connect(self.__on_select)
        layout.addWidget(self.__dir_preview)
        
        self.__error_label = QLabel(parent=self, text="")
        layout.addWidget(self.__error_label)
        
        self.__button = QPushButton(parent=self, text="Create")
        layout.addWidget(self.__button)
        self.__button.clicked.connect(self.accept)

        self.accepted.connect(self.__on_accept)

        self.__item_type = item_type
        self.__wiki_directory = wiki_proper_directory
        self.__validate()
        # Width of self.__location_label is inaccurate when retrieved in __init__, it must be running on the app for it to be accurate
        # QTimer.singleShot(10, Qt.TimerType.PreciseTimer, self.__update_item_label)
        
    def __on_accept(self):
        self.on_name_selected.emit(ItemCreationResult(
                path=self.gen_resultatnt_path(),
                typ=self.__item_type
            )
        )

    def __on_select(self):
        if chosen_dir := self.__dir_preview.get_chosen_dir():
            self.__working_directory = self.__wiki_directory / chosen_dir
        self.__validate()

    def gen_resultatnt_path(self):
        line_edit_txt = self.__line_edit.text()
        txt_stripped = line_edit_txt.strip()
        ending = ""
        if self.__item_type == ItemType.PWE:
            ending = ".pwe"
        return self.__working_directory / f"{txt_stripped}{ending}"

    def __validate(self):
        valid = True
        error_msg = ""
        line_edit_txt = self.__line_edit.text()
        if not valid_item_name(line_edit_txt):
            valid = False
            error_msg = "Not a valid item name."

        if (self.__wiki_directory / self.gen_resultatnt_path()).exists():
            valid = False
            error_msg = f"Item/folder already exists"
        valid = valid and self.__dir_preview.get_chosen_dir() is not None
        self.__error_label.setText(error_msg)
        self.__button.setDisabled(not valid)
        
            