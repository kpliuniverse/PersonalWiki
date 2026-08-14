import pathlib

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget
import sip

class ItemPanel(QWidget):

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

    def __clear_widget(self):
        layout = self.layout()
        assert layout is not None
        for child in self.findChildren(QWidget, "", Qt.FindChildOption.FindDirectChildrenOnly):
            child.deleteLater()
            
    

