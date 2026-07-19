import json
from typing import Dict

from PyQt6.QtWidgets import (
    QApplication,
)

from PyQt6.QtGui import QStandardItemModel, QFontDatabase
import sys
import pathlib 
import logging

from src.components.mainwindow import MainWindow
from src.states.appstate import AppState

FONT_PATH = pathlib.Path("assets/fonts")


class App:
    app: QApplication
    main_window: MainWindow
    app_state: AppState = AppState()
    def init_fonts(self): 
        for path in FONT_PATH.iterdir():
            QFontDatabase.addApplicationFont(path.as_posix())
            logging.info(f"Added font file: {path.as_posix()}")   
    
    def load_cur_file(self, file: pathlib.Path):
        self.app_state.cur_file = file
        self.main_window.load_cur_file()    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.init_fonts()
        self.main_window = MainWindow()
        
        self.app_state.cur_wiki = pathlib.Path(self.app.arguments()[1])
        #TODO: Use custom projectitemmodel
        self.main_window.set_app_state(self.app_state)
        self.main_window.refresh_project_tree()

        with open(self.app_state.cur_wiki.parent / ".pw" / "session.json") as session_file:
            session_json = json.load(session_file)
            self.load_cur_file(self.app_state.cur_wiki.parent / "proper" / session_json["currentFile"])

           
        
    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())    