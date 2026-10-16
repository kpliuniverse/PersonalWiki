import logging
import pathlib

from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QWidget, QVBoxLayout
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtCore import QTimer, Qt, pyqtSignal


from src.exceptions import GUIException
from src.items.items import ItemRecognizedType, ItemCreationResult
from src.ui.components.dir_preview import ProjectDirPreview
from src.utils.item_validity import is_valid_item_name
from src.wiki.wiki import Wiki

class ItemNewDialog(QDialog):

    on_name_selected: pyqtSignal = pyqtSignal(ItemCreationResult)

    
    def __init__(self, parent: QWidget, item_type: ItemRecognizedType, directory: pathlib.Path, wiki: Wiki) -> None:
        logging.debug("directory=%s, wiki_proper=%s", directory, wiki)

        self.__working_directory: pathlib.Path = directory
        super().__init__(parent)
        self.setWindowTitle("New Item")

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setFixedSize(400, 200)
        label = QLabel(parent=self, text="Enter your item/folder name")
        layout.addWidget(label)


        self.__line_edit = QLineEdit(self)
        self.__line_edit.textChanged.connect(self.__validate)
        layout.addWidget(self.__line_edit)

        self.__dir_preview = ProjectDirPreview(self, wiki, pre_chosen_dir=directory)
        self.__dir_preview.file_selected.connect(self.__on_select)
        layout.addWidget(self.__dir_preview)
        
        self.__error_label = QLabel(parent=self, text="")
        layout.addWidget(self.__error_label)
        
        self.__button = QPushButton(parent=self, text="Create")
        layout.addWidget(self.__button)
        self.__button.clicked.connect(self.accept)

        self.accepted.connect(self.__on_accept)

        self.__item_type: ItemRecognizedType = item_type
        self.__wiki = wiki
        # self.__wiki_directory: pathlib.Path = wiki
        self.__validate()
        # Width of self.__location_label is inaccurate when retrieved in __init__, it must be running on the app for it to be accurate
        # QTimer.singleShot(10, Qt.TimerType.PreciseTimer, self.__update_item_label)
        
    def __on_accept(self) -> None:
        self.on_name_selected.emit(ItemCreationResult(
                path=self.gen_resultant_path(),
                recognized_type=self.__item_type
            )
        )

    def __on_select(self) -> None:
        if (chosen_dir := self.__dir_preview.get_chosen_dir()) is not None:
            self.__working_directory: pathlib.Path = chosen_dir
        self.__validate()

    def gen_resultant_path(self) -> pathlib.Path:
        """
            Get resultant path, relative to wiki proper
        """
        line_edit_txt: str = self.__line_edit.text()
        txt_stripped: str = line_edit_txt.strip()
        ending: str = ""
        if self.__item_type == ItemRecognizedType.PWE:
            ending = ".pwe"
        return self.__working_directory / f"{txt_stripped}{ending}"

    def __validate(self) -> None:
        valid = True
        error_msg: str = ""
        line_edit_txt: str = self.__line_edit.text()
        if not is_valid_item_name(line_edit_txt):
            valid = False
            error_msg = "Not a valid item name."
        elif self.__dir_preview.get_chosen_dir() is None:
            valid = False
        elif self.__wiki.exists(self.gen_resultant_path()):
            valid = False
            error_msg: str = f"Item/folder already exists"
        self.__error_label.setText(error_msg)
        self.__button.setDisabled(not valid)
        
            