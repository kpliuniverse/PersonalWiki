import logging
import pkgutil
from typing import Any, Dict

import jinja2

from src.utils.custom_filters import res_path
from src.utils.package_utils import get_data_and_raise_if_none
from src.utils.singleton import Singleton


class MainHTMLTemplater(metaclass=Singleton):

    def __init__(self):
        self.__environment = jinja2.Environment()
        self.__environment.filters["res_path"] = res_path
        logging.info("Loading template.html")
        self.__template = self.__environment.from_string(get_data_and_raise_if_none("src.templating", "template.html").decode())
        # self.__css_template = self.__environment.from_string(get_data_and_raise_if_none("src.stati", "default_wiki.css").decode())

    def render(self, context: Dict[str, Any]):
        """
            Render the HTML file

            context should include:
            
            `body`: the body of the page 
        """
        
        return self.__template.render(context)
