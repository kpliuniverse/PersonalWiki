import datetime
import logging
import pathlib
from importlib import resources
from typing import Optional

from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6 import sip
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QGridLayout,
    QMainWindow,
    QSplitter,
    # QTextEdit,
    QWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QAction, QFont, QKeySequence, QShortcut
from PyQt6.QtCore import (
    Q_ARG, 
    QMetaObject, 
    QModelIndex, 
    QTimer, 
    QUrl, 
    Qt, 
    pyqtSlot, 
    QThread
)
# from PyQt6.QtWebEngineCore import QWebEngineProfile

from src.ui.components.item_panel import ItemPanel, ViewType
from src.ui.components.project_explorer import ProjectExplorer
from src.exceptions import GUIException
# from src.ui.pages.custom_page import CustomPage
from src.initcontext import InitContext
from src.states.appstate import AppState
from src.ui.components.entry_ribbon import EntryRibbon
from src.ui.utils.view_utils import guess_view_type
from src.ui.workers.renderer_worker import RendererWorker
from src.utils.navigation_info import NavigationInfo
from src.wiki.wiki import open_wiki
import src.ui.stylesheets as stylesheets
class MainWindow(QMainWindow):
                    
    def __init__(self, initcontext: InitContext):
        super().__init__()


        self.setStyleSheet("")
        self.setObjectName("MainWindow")
        self.setGeometry(200, 200, 1200, 800)
        self.setWindowTitle("PersonalWiki")

        self.__app_state = AppState()
        self.__app_state.cur_wiki = open_wiki(initcontext.path_to_pwi_file)

        #QOpenGLWidget(self) #dummy widget to prevent flickering
        self.__init_menu_bar()
        self.root = QWidget()
        self.__root_layout: QGridLayout = QGridLayout()
        self.root.setLayout(self.__root_layout)
                
        # ribbon = ItemRibbon(parent=self.root)
        # self.__root_layout.addWidget(ribbon)

        editor_splitter: QSplitter = QSplitter(parent=self.root)
        self.__root_layout.addWidget(editor_splitter, 1, 0, 8, 1)

        self.__project_explorer = ProjectExplorer(editor_splitter)
        self.__project_explorer.file_double_clicked.connect(self.__on_project_item_double_clicked)
        self.__project_explorer.item_operation_requested.connect(self.__app_state.cur_wiki.do_operations)
        editor_splitter.addWidget(self.__project_explorer)

        self.__item_panel = ItemPanel(editor_splitter, self.__app_state.cur_wiki.get_wiki_dir_path())
        editor_splitter.addWidget(self.__item_panel)

        editor_splitter.setHandleWidth(16)
        editor_splitter.setSizes([20, 300])

        self.setCentralWidget(self.root)

        # self.__save_timer = QTimer()
        # self.__save_timer.setInterval(1000 * 60 * 5) #every five minutes
        # self.__save_timer.timeout.connect(self.__save_cur_item)
        # self.__save_timer.start()
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.__save_cur_item)

        # self.__load_cur_item()
        self.__refresh_project_tree()

        qss_file = resources.files(stylesheets) / "stylesheet.qss"
        with qss_file.open("r") as f:
            self.setStyleSheet(f.read())

    def __init_menu_bar(self):
        
        menu_bar = self.menuBar()
        if menu_bar is None:
            raise GUIException("Cannot fetch menu_bar of MainWindow, or is otherwise None")
            
        file_menu = menu_bar.addMenu("File")
        if file_menu is None:
            raise GUIException("Cannot fetch file_menu of menu_bar, or is otherwise None")
            
        
        actions = []

        for action_entry in actions:
            action = QAction(action_entry[0], self)
            action.triggered.connect(action_entry[1])
            file_menu.addAction(action)

    def __load_item(self, item_path: pathlib.Path):
        item_path_abs = self.__app_state.cur_wiki.get_wiki_proper_path() / item_path
        self.__app_state.cur_wiki.set_cur_item(item_path)
        self.__item_panel.load(guess_view_type(item_path_abs), item_path_abs)

    def __on_project_item_double_clicked(self, val: QModelIndex):
        item_path: pathlib.Path = val.data(Qt.ItemDataRole.UserRole + 1)
        item_path_abs = self.__app_state.cur_wiki.get_wiki_proper_path() / item_path
        logging.debug("Item double clicked to %s", item_path)
        if item_path_abs.is_file():
            self.__load_item(item_path)
  
    def __refresh_project_tree(self):
        proper_path = (self.__app_state.cur_wiki.get_wiki_dir_path() / "proper")
        self.__project_explorer.load(proper_path)
        
    def __update_status_bar(self, message: str, timeout_msec: int | None =None):
        if (status_bar := self.statusBar()) is not None:
            if timeout_msec is None:
                status_bar.showMessage(message)
            else:
                status_bar.showMessage(message, timeout_msec)
        else:
            raise GUIException("Error loading status bar")
    
    def __save_cur_item(self):
        if (item := self.__app_state.cur_wiki.get_cur_item_abs()) is None:
            return
        self.__item_panel.trigger_save()
        time = datetime.time.isoformat(datetime.datetime.today().time(), "seconds")
        self.__update_status_bar(f"Saved {item.as_posix()} at {time}", 5000)

    # def __load_cur_item(self):
    #     with open(self.__app_state.cur_wiki.get_cur_item_abs(), encoding="utf-8") as file:
    #         self.__text_edit.setText(file.read())
    #     self.__render_markdown()
    #     self.__save_timer.start()
