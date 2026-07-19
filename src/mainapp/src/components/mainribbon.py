from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

class MainRibbon(QWidget):
    compile_button: QPushButton
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.compile_button =  QPushButton(parent=self, text="Compile")
        self.layout().addWidget(self.compile_button) # pyright: ignore[reportOptionalMemberAccess]
   
