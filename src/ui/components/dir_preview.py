
import pathlib
from typing import Optional

from PyQt6.QtWidgets import  QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics

from ui.dialogs.project_dialog import ProjectDialog, ProjectDialogArgs
from src.utils.path_utils import gen_path_string

class DirPreview(QWidget):

    file_selected: pyqtSignal = pyqtSignal()
    def __init__(self, parent: QWidget, wiki_dir: pathlib.Path, pre_chosen_dir: Optional[pathlib.Path] = None):
        super().__init__(parent=parent)

        dir_chooser_layout = QHBoxLayout()
        self.setLayout(dir_chooser_layout)

        self.__location_label = QLabel(parent=self)
        dir_chooser_layout.addWidget(self.__location_label)

        browse_button = QPushButton(parent=self, text="Browse")
        browse_button.clicked.connect(self.__on_browse)
        dir_chooser_layout.addWidget(browse_button)

        QTimer.singleShot(10, lambda: self.__location_label.setText)
        self.__wiki_directory = wiki_dir
        self.__chosen_path: Optional[pathlib.Path] = None
        
        self.__update_label()

        if pre_chosen_dir is not None:
            self.__on_chosen(pre_chosen_dir)
        
    def __update_label(self):
        if self.__chosen_path is None:
            self.__location_label.setText("(no chosen path)")
            return
        location_text = f"at {gen_path_string(self.__wiki_directory / self.__chosen_path, self.__wiki_directory)}"
        metrics = QFontMetrics(self.__location_label.font())
        elided_text = metrics.elidedText(location_text, Qt.TextElideMode.ElideMiddle, self.__location_label.width())
        self.__location_label.setText(elided_text)

    def __on_chosen(self, chosen_path: pathlib.Path):
        self.__chosen_path = chosen_path
        self.__update_label()
        self.file_selected.emit()

    def get_chosen_dir(self):
        return self.__chosen_path

    def __on_browse(self):
        dialog = ProjectDialog(self, self.__wiki_directory, ProjectDialogArgs(
            dir_only=True,
            add_root_as_folder=True,

        ))
        dialog.on_file_selected.connect(self.__on_chosen)
        dialog.exec()
        
