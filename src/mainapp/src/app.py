import sys
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QTextEdit

class App:
    app: QApplication 
    widget: QWidget
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.widget = QWidget()
        grid: QGridLayout = QGridLayout()
        text_edit = QTextEdit()
        text_edit.setText("Hello World!")
        text_edit.setAcceptRichText(False)
        grid.addWidget(text_edit)
        self.widget.setLayout(grid)
        self.widget.setGeometry(200, 200, 1200, 800)
        self.widget.setWindowTitle("PersonalWiki")
        

    def run(self):
        self.widget.show()
        sys.exit(self.app.exec())