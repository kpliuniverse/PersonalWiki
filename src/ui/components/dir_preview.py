"""
    Module for dir previews: which display the current directory the user is selecting
"""
import pathlib
from typing import Callable, Optional

from PyQt6.QtWidgets import  QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics

from src.ui.dialogs.project_dialog import ProjectDialog, ProjectDialogArgs
from src.utils.path_utils import gen_path_string

class DirPreviewWidget(QWidget):
    button_clicked = pyqtSignal(int)

    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)

        self.__formating_function: Callable[[], str] = lambda: ""
        
        dir_chooser_layout = QHBoxLayout()
        self.setLayout(dir_chooser_layout)

        self.__location_label = QLabel(parent=self)
        dir_chooser_layout.addWidget(self.__location_label)

        self.browse_button = QPushButton(parent=self, text="Browse")
        self.browse_button.clicked.connect(self.button_clicked.emit)
        dir_chooser_layout.addWidget(self.browse_button)
        

    def set_location_text(self, text: str):
        metrics = QFontMetrics(self.__location_label.font())
        elided_text = metrics.elidedText(text, Qt.TextElideMode.ElideMiddle, self.__location_label.width())
        self.__location_label.setText(elided_text)

    def set_button_enabled(self, b: bool):
        self.browse_button.setDisabled(not b)


class ProjectDirPreview(QWidget):
    file_selected = pyqtSignal()
    def __init__(self, parent: QWidget, wiki_dir: pathlib.Path, pre_chosen_dir: Optional[pathlib.Path] = None):
        super().__init__(parent=parent)

        dir_chooser_layout = QHBoxLayout()
        self.setLayout(dir_chooser_layout)

        self.dir_preview_control = DirPreviewWidget(self)
        self.dir_preview_control.button_clicked.connect(self.__on_browse)
        dir_chooser_layout.addWidget(self.dir_preview_control)

        self.__wiki_directory = wiki_dir
        self.__chosen_path: Optional[pathlib.Path] = None

        if pre_chosen_dir is not None:
             self.__on_chosen(pre_chosen_dir)

        QTimer.singleShot(10, self.__update_label)
        
    def __update_label(self):
        if self.__chosen_path is None:
            self.dir_preview_control.set_location_text("(no path selected)")
            return
        location_text = f"at {gen_path_string(self.__wiki_directory / self.__chosen_path, self.__wiki_directory)}"
        self.dir_preview_control.set_location_text(location_text)

    def __on_chosen(self, chosen_path: pathlib.Path):
        self.__chosen_path = chosen_path
        self.__update_label()
        self.file_selected.emit()

    def get_chosen_dir(self):
        """
            Get chosen dir, relative to wiki proper.
        """
        return self.__chosen_path

    def __on_browse(self):
        dialog = ProjectDialog(self, self.__wiki_directory, ProjectDialogArgs(
            dir_only=True,
            add_root_as_folder=True,

        ))
        dialog.on_file_selected.connect(self.__on_chosen)
        dialog.exec()


class SystemDirPreview(QWidget):
    file_selected = pyqtSignal()
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)

        dir_chooser_layout = QHBoxLayout()
        self.setLayout(dir_chooser_layout)

        self.dir_preview_control = DirPreviewWidget(self)
        self.dir_preview_control.button_clicked.connect(self.__on_browse)
        dir_chooser_layout.addWidget(self.dir_preview_control)

        
        self.__chosen_path: Optional[pathlib.Path] = None

        QTimer.singleShot(10, self.__update_label)
        
    def __update_label(self):
        if self.__chosen_path is None:
            self.dir_preview_control.set_location_text("(no path selected)")
            return
        location_text = f"at {self.__chosen_path}"
        self.dir_preview_control.set_location_text(location_text)

    def __on_chosen(self, chosen_path: pathlib.Path):
        self.__chosen_path = chosen_path
        self.__update_label()
        self.file_selected.emit()

    def get_chosen_dir(self):
        """
            Get chosen dir, relative to wiki proper.
        """
        return self.__chosen_path

    def __on_browse(self):
        dialog = ProjectDialog(self, self.__wiki_directory, ProjectDialogArgs(
            dir_only=True,
            add_root_as_folder=True,

        ))
        dialog.on_file_selected.connect(self.__on_chosen)
        dialog.exec()
