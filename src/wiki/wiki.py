from dataclasses import dataclass
import dataclasses
from enum import IntEnum, auto
import json
import logging
import os
import pathlib
import shutil
from typing import List

from attr import define, field, setters
from returns.result import Failure, Result, Success

from src.exceptions import InvalidNameException
from src.states.wikistate import Session, Settings, WikiState
from src.utils.file_validity import valid_wiki_name
from src.utils.item_actions import Action, CopyAction, MoveAction, DeleteAction, NewItemAction
        
class Wiki:
    """
        Do not use the class directly. Use open_wiki and new_wiki instead
    """
    def __init__(self, path_dir: pathlib.Path, session: Session, settings: Settings):
        self.__wikistate = WikiState(
            cur_session=session,
            prev_settings=dataclasses.replace(settings),
            cur_settings=dataclasses.replace(settings),
            path_dir=path_dir
        )
        
    def get_wiki_dir_path(self):
        return self.__wikistate.path_dir

    def get_wiki_proper_path(self):
        return self.get_wiki_dir_path() / "proper"

    def do_operations(self, actions: List[Action]):
        """
            Given a list of actions, do move, copy, delete,
        """
        match actions:
            case []:
                return
            case [MoveAction(src, dst)]:
                logging.debug("Moving from %s to %s", src.as_posix(), dst.as_posix())
                shutil.move(self.get_wiki_proper_path() / src, self.get_wiki_proper_path() / dst)
            case [CopyAction(src, dst)]:
                logging.debug("Copying from %s to %s", src.as_posix(), dst.as_posix())
                shutil.copy(self.get_wiki_proper_path() / src, self.get_wiki_proper_path() / dst)
            case [DeleteAction(target)]:
                logging.debug("Deleting %s", target)
                if target.is_file():
                    os.remove(target)
                if target.is_dir():
                    shutil.rmtree(self.get_wiki_proper_path() / target)
            case [NewItemAction(target, is_dir)]:
                if is_dir:
                    logging.debug("Creating item dir %s", target)
                else:
                    logging.debug("Creating item %s", target)
                path = self.get_wiki_proper_path() / target
                if is_dir:
                    path.mkdir()
                else:
                    with open(path, "x", encoding="utf-8"):
                        pass

    def set_cur_item(self, item: pathlib.Path):
        self.__wikistate.cur_session.cur_item = item

    def get_cur_item(self):
        """
            Returns None if there are no items currently selected
        """
        return self.__wikistate.cur_session.cur_item

    def get_cur_item_abs(self):
        """
            Returns None if there are no items currently selected
        """
        cur_item = self.get_cur_item()
        if cur_item is None:
            return None
        return self.get_wiki_proper_path() / cur_item


def open_wiki(path_to_wiki_pwi_file: pathlib.Path) -> Wiki:

    if not path_to_wiki_pwi_file.exists():
        raise FileNotFoundError(f"{path_to_wiki_pwi_file.as_posix()} doesn't exist")
    
    """
        Open a wiki and return a Wiki object.
    """
    try:
        with open(path_to_wiki_pwi_file.parent / ".pw" / "session.json", encoding="utf-8") as session_file:
            session_json = json.load(session_file)
            session = Session(
                cur_item=session_json["currentFile"]
            )
    except FileNotFoundError:
        session = Session(
            cur_item=None
        )
    
    wiki = Wiki(
        path_dir=path_to_wiki_pwi_file.parent,
        session=session,
        settings=Settings()
    )

    return wiki


class CreateWikiErrors(IntEnum):
    """
        Error values when for one reason or another, create_wiki doesn't succeed
    """
    FILE_ALREADY_EXISTS = auto()
    INVALID_NAME = auto()

def create_wiki(dir_path: pathlib.Path, name: str):
    if not valid_wiki_name(name):
        raise InvalidNameException("Invalid name.")
    wiki_dir = dir_path / name
    wiki_dir.mkdir()
    (wiki_dir / "proper").mkdir()

    wiki_pwi = wiki_dir / "wiki.pwi"
    with open(wiki_pwi, "x", encoding="utf8"):
        pass

    return open_wiki(wiki_pwi)