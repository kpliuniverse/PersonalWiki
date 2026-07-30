
from dataclasses import dataclass
from enum import Enum
import pathlib
import re


class ItemType(Enum):
    PWE = 0
    FOLDER = 1

@dataclass
class ItemCreationResult:
    path: pathlib.Path
    typ: ItemType
