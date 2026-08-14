from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

class WikiEntryView(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.setLayout(QVBoxLayout())

        label = QLabel(parent=self, text="Test Entry View")
        if (l := self.layout()) is not None:
            l.addWidget(label)
