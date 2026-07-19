from PyQt6.QtGui import QFont, QStandardItem, QStandardItemModel

class ProjectItem(QStandardItem):
    def __init__(self):
        super().__init__()
        self.setEditable(False)
    