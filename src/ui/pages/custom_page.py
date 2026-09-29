import logging
from typing import override

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEnginePage

from src.consts import LOOPBACK_IP_ADD
from src.utils.navigation_info import NavigationInfo

class CustomPage(QWebEnginePage):

    navigation_requested: pyqtSignal = pyqtSignal(NavigationInfo)

    #TODO: Log JS messages, including info.
    @override
    def acceptNavigationRequest(self, url: QUrl, type: QWebEnginePage.NavigationType, isMainFrame: bool) -> bool:
        self.navigation_requested.emit(NavigationInfo(
            url=url,
            type=type,
            is_main_frame=isMainFrame
        ))
    
        return url.host() == LOOPBACK_IP_ADD or url.scheme() == "data"

    @override
    def javaScriptConsoleMessage(self, level: QWebEnginePage.JavaScriptConsoleMessageLevel, message: str | None, lineNumber: int, sourceID: str | None) -> None:
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel:
            logging.info("JS: %s", message)
        elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel:
            logging.warning("JS: %s", message)
        elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            logging.error("JS: Error at line %i: %s", lineNumber, message)
        
        super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)


