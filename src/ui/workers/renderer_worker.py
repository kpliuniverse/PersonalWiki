
import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.parser import markdown_parser

class RendererWorker(QObject):

    """
        Dedicated worker for pwe rendering
    """
    
    finished: pyqtSignal = pyqtSignal(str)
    
    @pyqtSlot(str)    
    def render_pwe(self, pwe: str):
        logging.debug("Rendering")
        parsed = markdown_parser.parse_chunk(pwe)
        self.finished.emit(parsed)
        markdown_parser.parse_chunk(pwe)
        logging.debug("Done rendering")