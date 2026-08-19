import logging
import pathlib
from typing import Optional, override

from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Q_ARG, QMetaObject, QThread, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QLabel, QSplitter, QTextEdit, QVBoxLayout, QWidget

from src.consts import WIKI_ENCODING
from src.ui.components.entry_ribbon import EntryRibbon
from src.ui.pages.custom_page import CustomPage
from src.ui.utils.item_view_base import BaseItemView
from src.ui.workers.renderer_worker import RendererWorker
from src.utils.navigation_info import NavigationInfo

class WikiEntryView(BaseItemView):
    """
        Implements Loadable, Savable, CanSwitchToOtherItems
    """
    switch_signal = pyqtSignal(pathlib.Path)

    def __init__(self, parent, wiki_dir: pathlib.Path) -> None:
        self.__cur_item_path: Optional[pathlib.Path] = None
        super().__init__(parent)
        self.__wiki_dir = wiki_dir
        self.__rendering_thread: Optional[QThread] = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        entry_ribbon = EntryRibbon(self)
        layout.addWidget(entry_ribbon, stretch=1)
        entry_ribbon.render_button.clicked.connect(self.__on_render_button)


        editor_splitter: QSplitter = QSplitter(parent=self)
        layout.addWidget(editor_splitter, stretch=8)

        self.__text_edit = QTextEdit(editor_splitter)
        self.__text_edit.setAcceptRichText(False)
        self.__text_edit.setFont(QFont("Hack", 10, weight=6))
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

    def load_item(self, item: pathlib.Path):
        self.__cur_item_path = item
        with open(item, encoding=WIKI_ENCODING) as file:
            self.__text_edit.setText(file.read())
        self.__render_markdown()

    @pyqtSlot()
    def __render_markdown(self):
        if self.__rendering_thread is None:
            self.__rendering_thread = QThread()
        self.__text_view.setHtml("Loading...")
        if self.__rendering_thread.isRunning():
            self.__rendering_thread.requestInterruption()
        pwe_string = self.__text_edit.toPlainText()
        logging.debug("Preparing to render...")
        # TODO: Abstract thread creation.
        renderer_worker = RendererWorker()
        renderer_worker.moveToThread(self.__rendering_thread)
        self.__rendering_thread.started.connect(lambda: QMetaObject.invokeMethod(renderer_worker, "render_pwe", Qt.ConnectionType.QueuedConnection, Q_ARG(str, pwe_string)))
        renderer_worker.finished.connect(self.__text_view.setHtml)
        renderer_worker.finished.connect(self.__rendering_thread.quit)
        self.__rendering_thread.finished.connect(renderer_worker.deleteLater)
        self.__rendering_thread.finished.connect(self.__cleanup_thread)
        self.__rendering_thread.start()

    
    def __cleanup_thread(self):
        if self.__rendering_thread:
            self.__rendering_thread.deleteLater()
            self.__rendering_thread = None

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
        assert self.__cur_item_path is not None
        with open(self.__cur_item_path, "w", encoding=WIKI_ENCODING) as file:
            file.write(self.__text_edit.toPlainText())


    
    def __on_render_button(self):
        self.save_cur_item()
        self.__render_markdown()