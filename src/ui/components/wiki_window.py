from PyQt6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget


class WikiWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PersonalWiki Wiki Manager")

        panel = QWidget(parent=self)
        self.setCentralWidget(panel)
        panel.setLayout(QVBoxLayout())

        new_button = QPushButton(parent=panel, text="New Wiki")

        open_button = QPushButton(parent=panel, text="Open Wiki")

        if l := panel.layout():
            l.addWidget(new_button)
            l.addWidget(open_button)
