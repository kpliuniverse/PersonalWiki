
from PyQt6.QtWidgets import (
    QApplication,
)

from PyQt6.QtGui import QFontDatabase

import sys
import pathlib 
import logging

from src.initcontext import InitContext
from src.ui.components.main_window import MainWindow
from src.ui.components.wiki_window import WikiWindow

FONT_PATH = pathlib.Path("assets/fonts")


class App:

    def init_fonts(self): 
        for path in FONT_PATH.iterdir():
            QFontDatabase.addApplicationFont(path.as_posix())
            logging.info("Added font file: %s", path.as_posix())

    def __init__(self):
        self.main_window: MainWindow | None  = None
        self.app = QApplication(sys.argv)

    def run_main(self, wiki: pathlib.Path):
        self.main_window = MainWindow(initcontext=InitContext(
            path_to_pwi_file=pathlib.Path(wiki)
        ))
        self.main_window.show()

    def run(self):
        self.init_fonts()
        if len(self.app.arguments()) == 1:
            wiki_window = WikiWindow()
            wiki_window.wiki_opened.connect(self.run_main)
            wiki_window.show()
        else:
            self.run_main(pathlib.Path(self.app.arguments()[1]))

        sys.exit(self.app.exec())    