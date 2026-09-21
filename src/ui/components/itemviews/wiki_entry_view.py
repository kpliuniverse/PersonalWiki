import base64
import logging
import pathlib
from typing import Optional

from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Q_ARG, QMetaObject, QThread, QTimer, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QLabel, QSplitter, QTextEdit, QVBoxLayout, QWidget

from src.consts import LOOPBACK_IP_ADD, SAVE_DELAY_MS, WIKI_ENCODING
from src.multiprocessing.child_processes.webserver import WEBSERVER_PORT
from src.states.appstate import AppState
from src.ui.components.entry_ribbon import EntryRibbon
from src.ui.pages.custom_page import CustomPage
from src.ui.stylesheets.app_stylesheet import MainStylesheetManager
from src.ui.utils.item_view_base import BaseItemView
from src.utils.encoding import url_b64_encode
from src.utils.navigation_info import NavigationInfo



class WikiEntryView(BaseItemView):
    """
        Implements Loadable, Savable, CanSwitchToOtherItems
    """
    switch_signal = pyqtSignal(pathlib.Path)

    def __init__(self, parent, app_state: AppState) -> None:
        self.__cur_item_path: Optional[pathlib.Path] = None
        super().__init__(parent)
        #self.__wiki_dir = wiki_dir
        # self.__rendering_thread: Optional[QThread] = None

        self.__app_state = app_state

        layout = QVBoxLayout()
        self.setLayout(layout)

        entry_ribbon = EntryRibbon(self)
        layout.addWidget(entry_ribbon, stretch=1)
        entry_ribbon.render_button.clicked.connect(self.__save_and_render)


        editor_splitter: QSplitter = QSplitter(parent=self)
        layout.addWidget(editor_splitter, stretch=8)

        self.__text_edit = QTextEdit(editor_splitter)
        self.__text_edit.setAcceptRichText(False)
        self.__text_edit.setAcceptDrops(False)
        self.__text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        editor_splitter.addWidget(self.__text_edit)
        
        self.__text_view = QWebEngineView(editor_splitter)
        self.profile = QWebEngineProfile()
        
        webpage = CustomPage(self.profile, self.__text_view)
        webpage.navigation_requested.connect(self.__intercept_navigation)
        self.__text_view.setPage(webpage)
        self.__text_view.show()
        editor_splitter.addWidget(self.__text_view)
        editor_splitter.setHandleWidth(16)
        editor_splitter.setSizes([100, 100])

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(SAVE_DELAY_MS)
        self.save_timer.timeout.connect(self.__save_and_render)
        self.setStyleSheet(MainStylesheetManager().get_rule("WikiEntryView"))
        self.__text_edit.textChanged.connect(self.__on_text_changed)

    def load_item(self, item: pathlib.Path):
        self.__cur_item_path = item
        #with open(self.__app_state.cur_wiki.get_wiki_proper_path() / item, encoding=WIKI_ENCODING) as file:
        self.__text_edit.setText(self.__app_state.cur_wiki.read_item(item))
        self.__render_markdown()

    def __on_text_changed(self):
        if not self.save_timer.isActive():
            self.save_timer.start()

    @pyqtSlot()
    def __render_markdown(self):
        if self.__cur_item_path is None:
            logging.warning("Tried to call __render_markdown while no file is opened")
            return
        # if self.__rendering_thread is None:
        #     self.__rendering_thread = QThread()
        self.__text_view.setHtml("Loading...")
        # if self.__rendering_thread.isRunning():
        #     self.__rendering_thread.requestInterruption()
        pwe_string = self.__text_edit.toPlainText()
        logging.debug("Preparing to render...")
        path = self.__cur_item_path.as_posix()
        logging.debug("path: %s", path)
        b64 = url_b64_encode(path.encode())
        url = QUrl(f"http://{LOOPBACK_IP_ADD}:{WEBSERVER_PORT}/view/{b64}")
        self.__text_view.setUrl(url)
        logging.info("Going to %s", url.toString())
        
        # # TODO: Abstract thread creation.
        # renderer_worker = RedirectorWorker()
        # renderer_worker.moveToThread(self.__rendering_thread)
        # self.__rendering_thread.started.connect(lambda: QMetaObject.invokeMethod(renderer_worker, "render_pwe", Qt.ConnectionType.QueuedConnection, Q_ARG(str, pwe_string)))
        # renderer_worker.finished.connect(self.__text_view.setHtml)
        # renderer_worker.finished.connect(self.__rendering_thread.quit)
        # self.__rendering_thread.finished.connect(renderer_worker.deleteLater)
        # self.__rendering_thread.finished.connect(self.__cleanup_thread)
        # self.__rendering_thread.start()

    
    # def __cleanup_thread(self):
    #     if self.__rendering_thread:
    #         self.__rendering_thread.deleteLater()
    #         self.__rendering_thread = None

    def __intercept_navigation(self, nav_info: NavigationInfo):
        scheme = nav_info.url.scheme()
        if scheme == "data":
            return
        if scheme == "wiki":
            # QUrl.path() truncates first member
            url_copy = QUrl(nav_info.url)
            url_copy.setScheme("")
            url_str = url_copy.toString().lstrip("/")
            logging.debug("url_str=%s", url_str)
            if (abs_path := self.__wiki_dir / "proper" / url_str).exists():
                self.switch_signal.emit(pathlib.Path(abs_path))
        logging.debug("Going to %s", nav_info.url.toString())

    def save_cur_item(self):
        """
            Save the currently open item
        """
        assert self.__cur_item_path is not None
        with open(self.__cur_item_path, "w", encoding=WIKI_ENCODING) as file:
            file.write(self.__text_edit.toPlainText())
    
    def __save_and_render(self):
        self.save_cur_item()
        self.__render_markdown()