from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.ui.utils.item_view_base import BaseItemView
from src.ui.utils.item_view_protocols import Loadable



class TestView(BaseItemView):

    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.setLayout(QVBoxLayout())

        label = QLabel(parent=self, text="Test Entry View")
        if (l := self.layout()) is not None:
            l.addWidget(label)
