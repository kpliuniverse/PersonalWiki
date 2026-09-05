
import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.parser import markdown_parser
from src.templating.templating import MainHTMLTemplater

class RendererWorker(QObject):

    """
        Dedicated worker for pwe rendering
    """
    
    finished: pyqtSignal = pyqtSignal(str)
    
    @pyqtSlot(str)    
    def render_pwe(self, pwe: str):
        logging.debug("Rendering")
        parsed = markdown_parser.parse_chunk(pwe)
        context = {
            "body": parsed
        }
        self.finished.emit(MainHTMLTemplater().render(context))
        markdown_parser.parse_chunk(pwe)
        logging.debug("Done rendering")