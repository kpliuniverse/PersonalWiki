import pathlib
from typing import override

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog

from src.ui.dialogs.new_wiki_dialog import NewWikiDialog
from src.wiki.wiki import create_wiki


class WikiWindow(QMainWindow):

    wiki_opened = pyqtSignal(pathlib.Path)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PersonalWiki Wiki Manager")

        panel = QWidget(parent=self)
        self.setCentralWidget(panel)
        panel.setLayout(QVBoxLayout())

        new_button = QPushButton(parent=panel, text="New Wiki")
        new_button.clicked.connect(self.__on_new_btn_clicked)
        if (l := panel.layout()) is not None:
            l.addWidget(new_button)

        open_button = QPushButton(parent=panel, text="Open Wiki")
        open_button.clicked.connect(self.__on_open_btn_clicked)
        if (l := panel.layout()) is not None:
            l.addWidget(open_button)

    def __on_new_btn_clicked(self):
        new_wiki_dialog = NewWikiDialog(self)
        new_wiki_dialog.on_name_selected.connect(self.__create_wiki_and_open)
        new_wiki_dialog.exec()

    def __on_open_btn_clicked(self):
        file_dialog = QFileDialog(parent=self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("wiki.pwi")
        file_dialog.fileSelected.connect(lambda p: self.__open_wiki(pathlib.Path(p)))
        file_dialog.exec()

    def __create_wiki_and_open(self, final_path: pathlib.Path):
        wiki = create_wiki(final_path.parent, final_path.name)
        self.__open_wiki(wiki.get_wiki_dir_path() / "wiki.pwi")

    def __open_wiki(self, pwi_file: pathlib.Path):
        self.close()
        self.wiki_opened.emit(pwi_file)
