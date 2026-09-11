
import logging

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot

from src.parser import markdown_parser

class RedirectorWorker(QObject):

    """
        Dedicated worker for pwe rendering
    """
    
    finished: pyqtSignal = pyqtSignal(QUrl)
    
    @pyqtSlot(str)    
    def render_pwe(self, pwe: str):
        logging.debug("Rendering")
        #parsed = markdown_parser.parse_chunk(pwe)
        self.finished.emit(parsed)
        markdown_parser.parse_chunk(pwe)
        logging.debug("Done rendering")