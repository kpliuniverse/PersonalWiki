from importlib import resources as impresources
import sys
import pathlib 
import logging

from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import (
    QApplication,
)

from PyQt6.QtGui import QFontDatabase
from src.consts import RESOURCE_PATH
from src.initcontext import InitContext
from src.resources import ResourceManager
from src.ui.components.main_window import MainWindow
from src.ui.components.wiki_window import WikiWindow




class App:

    def __init__(self):
        self.main_window: MainWindow | None  = None
        self.app = QApplication(sys.argv)

    def add_paths(self):
        QDir.addSearchPath("res", "resources/")

    def init_resources(self):
        ResourceManager()

    def init_fonts(self):
        """
            Initialize font to the application's resident QFontDatabase
        """
        for path in (RESOURCE_PATH / "fonts").iterdir():
            QFontDatabase.addApplicationFont(path.as_posix())
            logging.info("Added font file: %s", path.as_posix())

    def run_main(self, wiki: pathlib.Path):
        """
            Runs the main windows.
        """
        self.main_window = MainWindow(initcontext=InitContext(
            path_to_pwi_file=pathlib.Path(wiki)
        ))
        self.main_window.show()

    def run(self):
        """
            Runs the app
        """
        self.add_paths()
        self.init_fonts()
        self.init_resources()
        if len(self.app.arguments()) == 1:
            wiki_window = WikiWindow()
            wiki_window.wiki_opened.connect(self.run_main)
            wiki_window.show()
        else:
            self.run_main(pathlib.Path(self.app.arguments()[1]))

        sys.exit(self.app.exec())    