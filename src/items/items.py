
from enum import Enum
import pathlib
import re

from attrs import define


class ItemType(Enum):
    Pwe = 0
    Folder = 1

@define
class ItemCreationResult:
    path: pathlib.Path
    typ: ItemType
