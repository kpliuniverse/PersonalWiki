
from PyQt6.QtWidgets import QApplication, QSplitter, QWidget, QGridLayout, QTextEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView #pylint[ignore]
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QFont, QFontDatabase

import sys
import pathlib as pl


FONT_PATH = pl.Path("assets/fonts")
class App:
    app: QApplication
    widget: QWidget
    root_layout: QGridLayout

    editor_font: QFont = QFont()

    def init_fonts(self): 
        for path in FONT_PATH.iterdir():
            id = QFontDatabase.addApplicationFont(path.as_posix())
            print(QFontDatabase.applicationFontFamilies(id))
    def __init__(self):

        self.app = QApplication(sys.argv)
        self.init_fonts()

        self.root = QWidget()
        self.root_layout: QGridLayout = QGridLayout()
        self.root.setLayout(self.root_layout)
        self.root.setGeometry(200, 200, 1200, 800)
        self.root.setWindowTitle("PersonalWiki")

        editor_splitter: QSplitter = QSplitter(parent=self.root)
        self.root_layout.addWidget(editor_splitter, 0, 0)

        text_edit = QTextEdit(editor_splitter)
        text_edit.setText("Hello World!")
        text_edit.setAcceptRichText(False)
        text_edit.setFont(QFont("Hack", 10))
        editor_splitter.addWidget(text_edit)
        
        text_view = QWebEngineView(self.root)
        text_view.load(QUrl("http://www.qt.io"))
        text_view.show()
        editor_splitter.addWidget(text_view)
    def run(self):
        self.root.show()
        sys.exit(self.app.exec())

    