from PyQt6.QtWidgets import (
    QGridLayout, 
    QMainWindow, 
    QSplitter, 
    QTextEdit, 
    QWidget
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont
import mistune

from src.components.mainribbon import MainRibbon



class MainWindow(QMainWindow):
    widget: QMainWindow
    root_layout: QGridLayout
    text_edit: QTextEdit
    text_view: QWebEngineView

    def render_markdown(self):
        out = str(mistune.html(self.text_edit.toPlainText()))
        self.text_view.setHtml(out)


    def init_menu_bar(self):
        menu_bar = self.menuBar()
        if menu_bar is None:
            raise Exception("Cannot fetch menu_bar of MainWindow, or is otherwise None")
        file_menu = menu_bar.addMenu("File")
        if file_menu is None:
            raise Exception("Cannot fetch menu_bar of FileMenu, or is otherwise None")
        file_menu.addAction("Load")
        file_menu.addAction("Save")
        file_menu.addAction("Save as")


    def __init__(self):
        super().__init__()

        self.setGeometry(200, 200, 1200, 800)
        self.setWindowTitle("PersonalWiki")        

        self.init_menu_bar()
        self.root = QWidget()
        self.root_layout: QGridLayout = QGridLayout()
        self.root.setLayout(self.root_layout)
                
        ribbon = MainRibbon(parent=self.root)
        self.root_layout.addWidget(ribbon)
        ribbon.render_button.clicked.connect(self.render_markdown)

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

        self.setCentralWidget(self.root)