from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSplitter, QTextEdit, QVBoxLayout, QWidget

from src.ui.pages.custom_page import CustomPage
class WikiEntryView(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        editor_splitter: QSplitter = QSplitter(parent=self)
        layout.addWidget(editor_splitter)

        self.__text_edit = QTextEdit(editor_splitter)
        self.__text_edit.setAcceptRichText(False)
        self.__text_edit.setFont(QFont("Hack", 10, weight=6))
        self.__text_edit.setAcceptDrops(False)
        self.__text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        editor_splitter.addWidget(self.__text_edit)
        
        self.__text_view = QWebEngineView(editor_splitter)
        # self.profile = QWebEngineProfile()
        
        # webpage = CustomPage(self.profile, self.__text_view)
        # # webpage.navigation_requested.connect(self.__intercept_navigation)
        # self.__text_view.setPage(webpage)
        # self.__text_view.show()
        editor_splitter.addWidget(self.__text_view)
        editor_splitter.setSizes([100, 100])

        
