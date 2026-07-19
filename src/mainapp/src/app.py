import json

from PyQt6.QtWidgets import (
    QApplication,
)

from PyQt6.QtGui import QFileSystemModel, QFontDatabase
import sys
import pathlib 
import logging

from src.components.mainwindow import MainWindow


FONT_PATH = pathlib.Path("assets/fonts")
class App:
    app: QApplication
    main_window: MainWindow
    cur_wiki: pathlib.Path
    cur_file: pathlib.Path
    def init_fonts(self): 
        for path in FONT_PATH.iterdir():
            QFontDatabase.addApplicationFont(path.as_posix())
            logging.info(f"Added font file: {path.as_posix()}")   
    

    def refresh_project_tree(self):
        file_system_model = QFileSystemModel()
        file_system_model.setRootPath((self.cur_wiki.parent / "proper").as_posix())
        self.main_window.refresh_file_tree(file_system_model)


    def load_cur_file(self, file: pathlib.Path):
        self.cur_file = file
        self.main_window.load_file(self.cur_file)    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.init_fonts()
        self.main_window = MainWindow()
        self.cur_wiki = pathlib.Path(self.app.arguments()[1])
        #TODO: Use custom projectitemmodel
        self.refresh_project_tree()

        with open(self.cur_wiki.parent / ".pw" / "session.json") as session_file:
            session_json = json.load(session_file)
            self.load_cur_file(self.cur_wiki.parent / "proper" / session_json["currentFile"])

           
        
    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())    