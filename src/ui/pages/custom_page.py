from typing import override

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEnginePage

from src.utils.navigation_info import NavigationInfo

class CustomPage(QWebEnginePage):

    navigation_requested: pyqtSignal = pyqtSignal(NavigationInfo)

    @override
    def acceptNavigationRequest(self, url: QUrl, type: QWebEnginePage.NavigationType, isMainFrame: bool) -> bool:
        self.navigation_requested.emit(NavigationInfo(
            url=url,
            type=type,
            is_main_frame=isMainFrame
        ))
        return url.scheme() == "data"