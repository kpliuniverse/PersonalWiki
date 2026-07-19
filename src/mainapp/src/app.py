from PyQt6.QtWidgets import (
    QApplication,
)

from PyQt6.QtGui import QFontDatabase
import sys
import pathlib as pl
import logging

from src.components.mainwindow import MainWindow


FONT_PATH = pl.Path("assets/fonts")
class App:
    app: QApplication
    main_window: MainWindow
    def init_fonts(self): 
        for path in FONT_PATH.iterdir():
            QFontDatabase.addApplicationFont(path.as_posix())
            logging.info(f"Added font file: {path.as_posix()}")   
    

    # def init_menu_bar(self):
    #     menu_bar = self.root.menuBar()
    #     if menu_bar is None:
    #         raise Exception("Cannot fetch menu_bar of MainWindow, or is otherwise None")
    #     file_menu = menu_bar.addMenu("File")
    #     if file_menu is None:
    #         raise Exception("Cannot fetch menu_bar of FileMenu, or is otherwise None")
    #     file_menu.addAction(text="Load")
    #     file_menu.addAction(text="Save")
    #     file_menu.addAction(text="Save as")

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.init_fonts()

        self.main_window = MainWindow()

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())

    