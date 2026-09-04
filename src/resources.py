import csv
from enum import StrEnum, auto
from importlib import resources as impresources
import logging
import pathlib
from typing import Any, Dict, List

from PyQt6.QtGui import QIcon
import attrs

from src.consts import RESOURCE_PATH
from src.exceptions import ResourceNotFoundError, ResourceTypeException
from src.utils.singleton import Singleton

class ResourceType(StrEnum):
    ICON = auto()

@attrs.define
class Resource:
    """
        Resource class

        type: the type of resource
        resource
    """
    type: ResourceType
    res: Any

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
                    res = QIcon(f"res:{path}")
                self.__resources[path] = Resource(
                    type=res_type,
                    res=res
                )
                logging.info("Loaded %s", path)

    def get(self, path: str):
        try:
            return self.__resources[path]
        except KeyError as exc:
            raise ResourceNotFoundError(f"Resource {path} not found or loaded.") from exc

