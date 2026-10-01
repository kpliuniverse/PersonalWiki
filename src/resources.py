import csv
from enum import StrEnum, auto
from importlib import resources as impresources
import logging
import pathlib
from typing import Any, Dict, List, Optional, TypeVar

from PyQt6.QtGui import QIcon
import attrs

from src.consts import RESOURCE_PATH
from src.utils.singleton import Singleton



class ResourceTypeAssertionException(BaseException):
    pass

class ResourceNotFoundError(BaseException):
    pass

class ResourceType(StrEnum):
    ICON = "icon"

@attrs.define
class Resource:
    """
        Resource class

        type: the type of resource
        resource
    """
    type: ResourceType
    res: Any
 
T = TypeVar("T")

class ResourceManager(metaclass=Singleton):
    """
        Resource manager singleton
    """
    def __init__(self) -> None:
        self.__resources: Dict[str, Resource] = dict()
        resource_csv = RESOURCE_PATH / "resources.csv"

        with open(resource_csv, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")

            for row in reader:
                path = row[0]
                res_type = ResourceType(row[1])

                if path in self.__resources:
                    raise KeyError(f"'{path}' defined twice.")
                res = None
                if res_type == ResourceType.ICON:
                    # Store the icon path; instantiate QIcon lazily to avoid QPixmap
                    # creation before a QGuiApplication exists
                    res_path = RESOURCE_PATH / path
                    res = str(res_path)
                else:
                    logging.warning("Unknown resource type of '%s' : %s", path, res_type)
                    continue
                self.__resources[path] = Resource(
                    type=res_type,
                    res=res
                )
                logging.info("Loaded %s", path)

    def assert_get_res(self, path: str, assert_res_type: Optional[ResourceType] = None, assert_type: Optional[type[T]] = None) -> T:
        res = self.get(path)
        if assert_res_type is not None and res.type != assert_res_type:
            raise ResourceTypeAssertionException(f"'{path}' expected to be ResourceType {assert_res_type}, is {res.type}")

        # If caller expects a specific runtime type (like QIcon), ensure the
        # resource is instantiated now.
        if assert_type is not None and res.type == ResourceType.ICON and isinstance(res.res, str):
            # instantiate QIcon from stored path
            res.res = QIcon(res.res)

        if assert_type and not isinstance(res.res, assert_type):
            raise TypeError(f"'{path}' expected to be type {assert_type}, is {type(res.res)}")       
        return res.res


    def get(self, path: str):
        try:
            res = self.__resources[path]
            # Lazy instantiate icons on direct get() as well
            if res.type == ResourceType.ICON and isinstance(res.res, str):
                res.res = QIcon(res.res)
            return res
        except KeyError as exc:
            raise ResourceNotFoundError(f"Resource {path} not found or loaded.") from exc

