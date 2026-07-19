
from PyQt6.QtWidgets import QApplication, QSplitter, QWidget, QGridLayout, QTextEdit, QHBoxLayout, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView 
from PyQt6.QtCore import QSize, QUrl
from PyQt6.QtGui import QFont, QFontDatabase
import mistune

import sys
import pathlib as pl

from src.components.mainribbon import MainRibbon


FONT_PATH = pl.Path("assets/fonts")
class App:
    app: QApplication
    widget: QWidget
    root_layout: QGridLayout

    editor_font: QFont = QFont()


    text_edit: QTextEdit
    text_view: QWebEngineView
    def init_fonts(self): 
        for path in FONT_PATH.iterdir():
            id = QFontDatabase.addApplicationFont(path.as_posix())
    
    def render(self):
        out = str(mistune.html(self.text_edit.toPlainText()))
        self.text_view.setHtml(out)
    
    def __init__(self):
        
        self.app = QApplication(sys.argv)
        self.init_fonts()

        self.root = QWidget()
        self.root_layout: QGridLayout = QGridLayout()
        self.root.setLayout(self.root_layout)
        self.root.setGeometry(200, 200, 1200, 800)
        self.root.setWindowTitle("PersonalWiki")
        
        ribbon = MainRibbon(parent=self.root)
        self.root_layout.addWidget(ribbon)
        ribbon.render_button.clicked.connect(self.render)

        editor_splitter: QSplitter = QSplitter(parent=self.root)
        self.root_layout.addWidget(editor_splitter, 1, 0, 8, 1)

        self.text_edit = QTextEdit(editor_splitter)
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setFont(QFont("Hack", 10, weight=6))
        editor_splitter.addWidget(self.text_edit)
        
        self.text_view = QWebEngineView(self.root)
        self.text_view.show()
        editor_splitter.addWidget(self.text_view)

        self.text_view.setMinimumWidth(256)
        editor_splitter.setHandleWidth(16)
        editor_splitter.setSizes([200, 80])
    def run(self):
        self.root.show()
        sys.exit(self.app.exec())

    