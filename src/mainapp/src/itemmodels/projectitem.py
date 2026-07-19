from PyQt6.QtGui import QFont, QStandardItem, QStandardItemModel

class ProjectItem(QStandardItem):
    def __init__(self, text):
        super().__init__()
        self.setEditable(False)
        self.setText(text)
    