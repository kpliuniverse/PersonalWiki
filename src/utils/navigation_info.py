from attrs import define

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEnginePage

@define
class NavigationInfo:
    url: QUrl
    type: QWebEnginePage.NavigationType
    is_main_frame: bool