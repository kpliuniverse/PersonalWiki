

import pathlib

from attrs import define, field, setters


@define(slots=True)
class Session:
    cur_item: pathlib.Path


@define(slots=True)
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