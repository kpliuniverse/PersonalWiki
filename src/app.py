
from PyQt6.QtWidgets import (
    QApplication,
)

from PyQt6.QtGui import QFontDatabase

import sys
import pathlib 
import logging

from src.initcontext import InitContext
from src.ui.components.main_window import MainWindow

FONT_PATH = pathlib.Path("assets/fonts")


class App:

    def init_fonts(self): 
        for path in FONT_PATH.iterdir():
            QFontDatabase.addApplicationFont(path.as_posix())
            logging.info("Added font file: %s", path.as_posix())   

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.init_fonts()
        self.main_window = MainWindow(initcontext=InitContext(
            wiki=pathlib.Path(self.app.arguments()[1])
        ))

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())    