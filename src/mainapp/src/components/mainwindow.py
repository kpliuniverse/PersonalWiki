from collections import deque
import pathlib
from typing import Deque, Dict, List

from PyQt6.QtWidgets import (
    QGridLayout, 
    QMainWindow, 
    QSplitter, 
    QTextEdit,
    QTreeView, 
    QWidget,    
)

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QAction, QFileSystemModel, QFont, QStandardItem, QStandardItemModel
from PyQt6.QtCore import QModelIndex, Qt
import mistune

from src.states.appstate import AppState
from src.components.mainribbon import MainRibbon
from src.itemmodels.projectitem import ProjectItem

class MainWindow(QMainWindow):

    __root_layout: QGridLayout
    __text_edit: QTextEdit
    __text_view: QWebEngineView
    __project_tree: QTreeView
    __app_state: AppState

    def render_markdown(self):
        out = str(mistune.html(self.__text_edit.toPlainText()))
        self.__text_view.setHtml(out)

    def init_menu_bar(self):
        menu_bar = self.menuBar()
        if menu_bar is None:
            raise Exception("Cannot fetch menu_bar of MainWindow, or is otherwise None")
        file_menu = menu_bar.addMenu("File")
        if file_menu is None:
            raise Exception("Cannot fetch file_menu of menu_bar, or is otherwise None")
        

        actions = [
  #          ("Load", self.load_file),
            ("Save", self.save_cur_file),
  #          ("Save as", self.save_as_file)
        ]

        for action_entry in actions:
            action = QAction(action_entry[0], self)
            action.triggered.connect(action_entry[1])
            file_menu.addAction(action)

    def on_double_clicked(self, val: QModelIndex):
        print(val.data(Qt.ItemDataRole.UserRole))
            
    def __init__(self):
        super().__init__()

        self.setGeometry(200, 200, 1200, 800)
        self.setWindowTitle("PersonalWiki")        

        self.init_menu_bar()
        self.root = QWidget()
        self.__root_layout: QGridLayout = QGridLayout()
        self.root.setLayout(self.__root_layout)
                
        ribbon = MainRibbon(parent=self.root)
        self.__root_layout.addWidget(ribbon)
        ribbon.render_button.clicked.connect(self.render_markdown)

        editor_splitter: QSplitter = QSplitter(parent=self.root)
        self.__root_layout.addWidget(editor_splitter, 1, 0, 8, 1)

        self.__project_tree = QTreeView(editor_splitter)
        self.__project_tree.doubleClicked.connect(self.on_double_clicked)
        editor_splitter.addWidget(self.__project_tree)

        self.__text_edit = QTextEdit(editor_splitter)
        self.__text_edit.setAcceptRichText(False)
        self.__text_edit.setFont(QFont("Hack", 10, weight=6))
        editor_splitter.addWidget(self.__text_edit)
        
        self.__text_view = QWebEngineView(self.root)
        self.__text_view.show()
        editor_splitter.addWidget(self.__text_view)

        editor_splitter.setHandleWidth(16)
        editor_splitter.setSizes([80, 200, 80])

        self.setCentralWidget(self.root)

    def refresh_project_tree(self):
        item_system_model = QStandardItemModel()
        root_node = item_system_model.invisibleRootItem()
        if root_node is None:
            raise Exception("Failed fetching root node")
        proper_path = (self.__app_state.cur_wiki.parent / "proper")

        dir_to_item: Dict[str, QStandardItem] = dict()
        
        subdirs: Deque[pathlib.Path] = deque([proper_path])
        dir_to_item[proper_path.as_posix()] = root_node
        while (len(subdirs) > 0):
            subdir = subdirs.popleft()
            for path in subdir.iterdir():
                if path.is_junction() and path.is_symlink():
                    continue
                project_item = ProjectItem(path)

                if path.is_dir():
                    subdirs.append(path)
                    dir_to_item[path.as_posix()] = project_item
                    dir_to_item[subdir.as_posix()].appendRow(project_item)
                
                if path.is_file():
                    dir_to_item[subdir.as_posix()].appendRow(project_item)

            self.__project_tree.setModel(item_system_model)
        

    def set_app_state(self, app_state: AppState):
        self.__app_state = app_state

    def save_cur_file(self):
        with open(self.__app_state.cur_file, "w") as file:
            file.write(self.__text_edit.toPlainText())

    def load_cur_file(self):
        with open(self.__app_state.cur_file) as file:
            self.__text_edit.setText(file.read())
        self.render_markdown()