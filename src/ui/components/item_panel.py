import pathlib
from typing import Dict, Optional

from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from src.ui.components.itemviews.test_view import TestView
from src.ui.components.itemviews.wiki_entry_view import WikiEntryView


class ItemPanel(QWidget):

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.__item_view: Optional[QWidget] = None
        self.__view_type = "blank"
        #self.__dummy_widget = QOpenGLWidget(self)
    

        # Had to preload all widgets because dynamically loading QWebEngineView causes flickering.
        self.__widget_dict: Dict[str, QWidget] = {
                    "wiki": WikiEntryView(self),
                    "test": TestView(self),
                    "blank": QWidget(self),
                    # to prevent flickering. this has to be assigned here becuase assigning outside the dictionary causes visual glitches
                    "DO NOT USE THIS": QOpenGLWidget(self)
        }

        for widget in self.__widget_dict.values():
            widget.hide()

        self.load(self.__view_type)


    def __clear_view(self):
        if self.__item_view is None:
            return
    
        self.__item_view.hide()
        layout = self.layout()
        assert layout is not None
        layout.removeWidget(self.__item_view)
        #self.__item_view.deleteLater()
        self.__item_view = None

    def load(self, view_type):
        """
            Loads an item into the panel
        """
        if self.__view_type == view_type:
            return
        
        if view_type in self.__widget_dict:
            self.__clear_view()
            self.__install_view(self.__widget_dict[view_type])

    def __install_view(self, view: QWidget):
        view.show()
        self.__item_view = view
        if (l := self.layout()) is not None:
            l.addWidget(self.__item_view)