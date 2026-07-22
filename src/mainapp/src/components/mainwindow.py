from collections import deque
import datetime
import json
import logging
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
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut, QStandardItem, QStandardItemModel
from PyQt6.QtCore import QModelIndex, QTimer, Qt

from src.helpers import markdownparser
from src.initcontext import InitContext
from src.states.appstate import AppState
from src.components.mainribbon import MainRibbon
from src.itemmodels.projectitem import ProjectItem

class MainWindow(QMainWindow):

    __root_layout: QGridLayout
    __text_edit: QTextEdit
    __text_view: QWebEngineView
    __project_tree: QTreeView
    __app_state: AppState
    __save_timer: QTimer
    
    # TODO: Serparate this
    def __render_markdown(self):
        self.__text_view.setHtml("Loading...")        
        self.__text_view.setHtml(markdownparser.parse_markdown(self.__text_edit.toPlainText()))
    
    def __on_render_button(self):
        self.__save_cur_file()
        self.__render_markdown()

    def __init_menu_bar(self):
        menu_bar = self.menuBar()
        if menu_bar is None:
            logging.error("Cannot fetch menu_bar of MainWindow, or is otherwise None")
            return
        file_menu = menu_bar.addMenu("File")
        if file_menu is None:
            logging.error("Cannot fetch file_menu of menu_bar, or is otherwise None")
            return
        
        actions = [
            ("Save", self.__save_cur_file),
        ]

        for action_entry in actions:
            action = QAction(action_entry[0], self)
            action.triggered.connect(action_entry[1])
            file_menu.addAction(action)
        
    def __on_project_item_double_clicked(self, val: QModelIndex):
        item_path = pathlib.Path(val.data(Qt.ItemDataRole.UserRole + 1))
        if item_path.is_file():
            self.__load_file(item_path)

    def __init__(self, initcontext: InitContext):
        super().__init__()

        self.setGeometry(200, 200, 1200, 800)
        self.setWindowTitle("PersonalWiki")        

        self.__app_state = AppState()
        self.__app_state.cur_wiki = initcontext.wiki

        self.__init_menu_bar()
        self.root = QWidget()
        self.__root_layout: QGridLayout = QGridLayout()
        self.root.setLayout(self.__root_layout)
                
        ribbon = MainRibbon(parent=self.root)
        self.__root_layout.addWidget(ribbon)
        ribbon.render_button.clicked.connect(self.__on_render_button)

        editor_splitter: QSplitter = QSplitter(parent=self.root)
        self.__root_layout.addWidget(editor_splitter, 1, 0, 8, 1)

        self.__project_tree = QTreeView(editor_splitter)
        self.__project_tree.doubleClicked.connect(self.__on_project_item_double_clicked)
        editor_splitter.addWidget(self.__project_tree)

        self.__text_edit = QTextEdit(editor_splitter)
        self.__text_edit.setAcceptRichText(False)
        self.__text_edit.setFont(QFont("Hack", 10, weight=6))
        self.__text_edit.setAcceptDrops(False)
        self.__text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        editor_splitter.addWidget(self.__text_edit)
        
        self.__text_view = QWebEngineView(self.root)
        self.__text_view.show()
        editor_splitter.addWidget(self.__text_view)

        editor_splitter.setHandleWidth(16)
        editor_splitter.setSizes([80, 100, 100])

        self.setCentralWidget(self.root)

        self.__save_timer = QTimer()
        self.__save_timer.setInterval(1000 * 60 * 5) #every five minutes
        self.__save_timer.timeout.connect(self.__save_cur_file)
        self.__save_timer.start()
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.__save_cur_file)
        with open(self.__app_state.cur_wiki.parent / ".pw" / "session.json") as session_file:
            session_json = json.load(session_file)
            self.__load_file(self.__app_state.cur_wiki.parent / "proper" / session_json["currentFile"])

        self.__refresh_project_tree()

    def __refresh_project_tree(self):
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
        
    def __update_status_bar(self, message: str, timeout_msec: int | None =None):
        if (status_bar := self.statusBar()) is not None:
            if timeout_msec is None:
                status_bar.showMessage(message)
            else:
                status_bar.showMessage(message, timeout_msec)  
        else:
            logging.error("Error loading status bar")
    
    def __save_cur_file(self):
        with open(self.__app_state.cur_file, "w") as file:
            file.write(self.__text_edit.toPlainText())
        time = datetime.time.isoformat(datetime.datetime.today().time(), "seconds")
        self.__update_status_bar(f"Saved {self.__app_state.cur_file} at {time}", 5000)

    def __load_file(self, cur_file: pathlib.Path):
        self.__app_state.cur_file = cur_file
        with open(self.__app_state.cur_file) as file:
            self.__text_edit.setText(file.read())
        self.__render_markdown()
        self.__save_timer.start()
