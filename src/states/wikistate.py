

from dataclasses import dataclass
import pathlib
from typing import Optional

from attrs import define, field, setters


@dataclass(slots=True)
class Session:
    cur_item: Optional[pathlib.Path]


@dataclass(slots=True)
class Settings:
    """
        Contains the settings for the p
    """

@define    
class WikiState:
    cur_session: Session
    path_dir: pathlib.Path
    prev_settings: Settings = field(on_setattr=setters.frozen)
    cur_settings: Settings