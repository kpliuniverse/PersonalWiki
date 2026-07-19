from PyQt6.QtWidgets import (
    QApplication,
)

from PyQt6.QtGui import QFileSystemModel, QFontDatabase
import sys
import pathlib as pl
import logging

from src.components.mainwindow import MainWindow


FONT_PATH = pl.Path("assets/fonts")
class App:
    app: QApplication
    main_window: MainWindow
    cur_wiki: pl.Path
    def init_fonts(self): 
        for path in FONT_PATH.iterdir():
            QFontDatabase.addApplicationFont(path.as_posix())
            logging.info(f"Added font file: {path.as_posix()}")   
    

    def refresh_file_tree(self):
        file_system_model = QFileSystemModel()
        file_system_model.setRootPath(self.cur_wiki.parent.as_posix())
        self.main_window.refresh_file_tree(file_system_model)


    def __init__(self):
        self.app = QApplication(sys.argv)
        self.init_fonts()
        self.main_window = MainWindow()
        self.cur_wiki = pl.Path(self.app.arguments()[1])
        self.refresh_file_tree()
        
    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())

    