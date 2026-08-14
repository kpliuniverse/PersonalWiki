from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

class EntryRibbon(QWidget):

    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.render_button =  QPushButton(parent=self, text="&Render")
        self.layout().addWidget(self.render_button) # pyright: ignore[reportOptionalMemberAccess] 
