
from dataclasses import dataclass
import pathlib


@dataclass(frozen=True)
class InitContext:
    wiki: pathlib.Path