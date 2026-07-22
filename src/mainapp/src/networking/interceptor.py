from typing import override

from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInfo, QWebEngineUrlRequestInterceptor

class Interceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent):
        super().__init__(parent)

    @override
    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        info.requestUrl(