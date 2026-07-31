import datetime
import json
import logging
import pathlib
from typing import Optional

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QGridLayout, 
    QMainWindow, 
    QSplitter, 
    QTextEdit, 
    QWidget,    
)

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PyQt6.QtCore import Q_ARG, QMetaObject, QModelIndex, QObject, QTimer, Qt, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtWebEngineCore import QWebEngineProfile

from src.exceptions import GUIException
from src.pages.custompage import CustomPage
from src.initcontext import InitContext
from src.states.appstate import AppState
from src.components.mainribbon import MainRibbon
from src.components.projecttree import ProjectTree
from src.workers.rendererworker import RendererWorker

class MainWindow(QMainWindow):

    __root_layout: QGridLayout
    __text_edit: QTextEdit
    __text_view: QWebEngineView
    __project_tree:  ProjectTree
    __app_state: AppState
    __save_timer: QTimer

    __rendering_thread: Optional[QThread] = None
        
    @pyqtSlot()
    def __render_markdown(self):
        if self.__rendering_thread is None:
            self.__rendering_thread = QThread()
        self.__text_view.setHtml("Loading...")
        if self.__rendering_thread.isRunning():
            self.__rendering_thread.requestInterruption()
        pwe_string = self.__text_edit.toPlainText()
        logging.debug("Preparing to render...")
        renderer_worker = RendererWorker()
        renderer_worker.moveToThread(self.__rendering_thread)
        self.__rendering_thread.started.connect(lambda: QMetaObject.invokeMethod(renderer_worker, "render_pwe",Qt.ConnectionType.QueuedConnection, Q_ARG(str, pwe_string)))
        renderer_worker.finished.connect(self.__text_view.setHtml)
        renderer_worker.finished.connect(self.__rendering_thread.quit)
        self.__rendering_thread.finished.connect(renderer_worker.deleteLater)
        self.__rendering_thread.finished.connect(self.__cleanup_thread)
        self.__rendering_thread.start()

    def __cleanup_thread(self):
        if self.__rendering_thread:
            self.__rendering_thread.deleteLater()
            self.__rendering_thread = None

    def __on_render_button(self):
        self.__save_cur_file()
        self.__render_markdown()

    def __init_menu_bar(self):
        
        menu_bar = self.menuBar()
        if menu_bar is None:
            raise GUIException("Cannot fetch menu_bar of MainWindow, or is otherwise None")
            return
        file_menu = menu_bar.addMenu("File")
        if file_menu is None:
            raise GUIException("Cannot fetch file_menu of menu_bar, or is otherwise None")
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
        ribbon.render_button.clicked.connect(self.__on_render_button, type=QtCore.Qt.ConnectionType.QueuedConnection)

        editor_splitter: QSplitter = QSplitter(parent=self.root)
        self.__root_layout.addWidget(editor_splitter, 1, 0, 8, 1)

        self.__project_tree = ProjectTree(editor_splitter)
        self.__project_tree.file_double_clicked.connect(self.__on_project_item_double_clicked)
        editor_splitter.addWidget(self.__project_tree)

        self.__text_edit = QTextEdit(editor_splitter)
        self.__text_edit.setAcceptRichText(False)
        self.__text_edit.setFont(QFont("Hack", 10, weight=6))
        self.__text_edit.setAcceptDrops(False)
        self.__text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        editor_splitter.addWidget(self.__text_edit)
        
        self.__text_view = QWebEngineView(self.root)
        self.profile = QWebEngineProfile()

        webpage = CustomPage(self.profile, self.__text_view)
        self.__text_view.setPage(webpage)
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
        proper_path = (self.__app_state.cur_wiki.parent / "proper")
        self.__project_tree.load(proper_path)

        
    def __update_status_bar(self, message: str, timeout_msec: int | None =None):
        if (status_bar := self.statusBar()) is not None:
            if timeout_msec is None:
                status_bar.showMessage(message)
            else:
                status_bar.showMessage(message, timeout_msec)  
        else:
            raise Exception("Error loading status bar")
    
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
