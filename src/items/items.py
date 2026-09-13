
from enum import Enum
import pathlib
import re

from attrs import define


class ItemRecognizedType(Enum):
    PWE = 0
    FOLDER = 1

@define
class ItemCreationResult:
    path: pathlib.Path
    recognized_type: ItemRecognizedType
