import pathlib
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6 import sip

from src.ui.components.itemviews.test_view import TestView
from src.ui.components.itemviews.wiki_entry_view import WikiEntryView


class ItemPanel(QWidget):

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.__view: Optional[QWidget] = None
        self.refresh("blank")

    def __clear_view(self):
        if self.__view is None:
            return
        layout = self.layout()
        assert layout is not None
        layout.removeWidget(self.__view)
        sip.delete(self.__view)
        self.__view = None


    def refresh(self, view_type):
        if view_type == "wiki":
            self.__clear_view()
            self.__install_view(WikiEntryView(self))
        if view_type == "test":
            self.__clear_view()
            self.__install_view(TestView(self))
        if view_type == "blank":
            self.__clear_view
            self.__install_view(QWidget(self))

    def __install_view(self, view: QWidget):
        self.__view = view
        if (l := self.layout()) is not None:
            l.addWidget(self.__view)