import pathlib
from typing import override

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog


class WikiWindow(QMainWindow):

    wiki_opened = pyqtSignal(pathlib.Path)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PersonalWiki Wiki Manager")

        panel = QWidget(parent=self)
        self.setCentralWidget(panel)
        panel.setLayout(QVBoxLayout())

        new_button = QPushButton(parent=panel, text="New Wiki")
        if (l := panel.layout()) is not None:
            l.addWidget(new_button)

        open_button = QPushButton(parent=panel, text="Open Wiki")
        open_button.clicked.connect(self.__on_open_btn_clicked)
        if (l := panel.layout()) is not None:
            l.addWidget(open_button)


    def __on_open_btn_clicked(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("wiki.pwi")
        file_dialog.fileSelected.connect(self.__open_wiki)
        file_dialog.exec()

    def __open_wiki(self, file: str):
        self.close()
        self.wiki_opened.emit(pathlib.Path(file))
