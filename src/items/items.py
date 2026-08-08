
from enum import Enum
import pathlib
import re

from attrs import define


class ItemType(Enum):
    PWE = 0
    FOLDER = 1

@define
class ItemCreationResult:
    path: pathlib.Path
    typ: ItemType
