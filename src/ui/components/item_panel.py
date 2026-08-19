from enum import StrEnum, auto
import pathlib
from typing import Dict, Optional

from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer, Qt, pyqtBoundSignal, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from src.ui.components.itemviews.blank_view import BlankView
from src.ui.components.itemviews.test_view import TestView
from src.ui.components.itemviews.wiki_entry_view import WikiEntryView
from src.ui.utils.item_view_base import BaseItemView
from src.ui.utils.item_view_protocols import CanSwitchToOtherItems, Loadable, Savable
from src.ui.utils.view_utils import ViewType, guess_view_type

    

class ItemPanel(QWidget):

    def __init__(self, parent: QWidget, wiki_dir: pathlib.Path):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.__item_view: Optional[BaseItemView] = None
        self.__view_type = ViewType.BLANK

        # to prevent flickering caused by the switch to OpenGL
        self.__dummy_widget = QOpenGLWidget(self)
        self.__dummy_widget.hide()

        # Had to preload all widgets because dynamically loading QWebEngineView causes flickering.
        self.__widget_dict: Dict[str, BaseItemView] = {
                    ViewType.ENTRY: WikiEntryView(self, wiki_dir),
                    ViewType.TEST: TestView(self),
                    ViewType.BLANK: BlankView(self),
        }

        for widget in self.__widget_dict.values():
            if isinstance(widget, CanSwitchToOtherItems):
                widget.switch_signal.connect(lambda x: self.load(guess_view_type(x), x))
            widget.hide()

        self.load(self.__view_type, pathlib.Path("."))

    def __clear_view(self):
        if self.__item_view is None:
            return
    
        self.__item_view.hide()
        layout = self.layout()
        assert layout is not None
        layout.removeWidget(self.__item_view)
        self.__item_view = None

    def __load_item(self, item: pathlib.Path):
        if isinstance(self.__item_view, Loadable):
            self.__item_view.load_item(item)
        

    def load(self, view_type: ViewType, item: pathlib.Path):
        """
            Loads an item into the panel
        """
        if self.__view_type == view_type:
            self.__load_item(item)
            return
        
        if view_type in self.__widget_dict:
            if self.__item_view is not None:
                self.__item_view.on_leave()
            self.__clear_view()
            self.__install_view(self.__widget_dict[view_type])
            self.__load_item(item)
            assert self.__item_view is not None
            self.__item_view.on_enter()

    def trigger_save(self):
        if isinstance(self.__item_view, Savable):
            self.__item_view.save_cur_item()

    def __install_view(self, view: BaseItemView):
        view.show()
        self.__item_view = view
        if (l := self.layout()) is not None:
            l.addWidget(self.__item_view)