from typing import override

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEnginePage

class CustomPage(QWebEnginePage):

    @override
    def acceptNavigationRequest(self, url: QUrl, type: QWebEnginePage.NavigationType, isMainFrame: bool) -> bool:
        return url.scheme() == "data"