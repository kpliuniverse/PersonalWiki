from dataclasses import dataclass
import dataclasses
from enum import IntEnum, StrEnum, auto
from io import TextIOWrapper
import json
import logging
import os
import pathlib
import shutil
from typing import IO, Any, List, Optional

from attr import define, field, setters
import attrs
from returns.result import Failure, Result, Success, attempt, safe
from sqlalchemy import Engine, create_engine

from src.consts import WIKI_ENCODING
from src.exceptions import InvalidNameException
from src.multiprocessing.multiprocessing import GlobalLock
from src.states.wikistate import Session, Settings, WikiState
from src.utils.file_utils import create_empty_file
from src.utils.item_validity import valid_item_name
from src.utils.item_actions import Action, CopyAction, MoveAction, DeleteAction, NewItemAction
from src.wiki.datamodel import WikiBase


NAME_OF_DB_FILE = "wiki.db"

class WikiFileMode(StrEnum):
    READ = "r"
    WRITE = "w"

class WikiFile:
    def __init__(self, path: pathlib.Path, mode: WikiFileMode):
        self.f: Optional[IO[Any]] = None
        self.path = path
        self.mode = mode

    def __enter__(self):
        self.f = open(self.path, mode=self.mode, encoding=WIKI_ENCODING)
        return self

    def __exit__(self, *args):
        if self.f is not None:
            self.f.close()
    
    def read(self):
        if self.f is None:
            raise IOError("No file opened")
        if self.mode != WikiFileMode.READ:
            raise IOError("Attempted to read a file meant for writing.")
        return self.f.read()

    def write(self, s: Any):
        if self.f is None:
            raise IOError("No file opened")
        if self.mode != WikiFileMode.WRITE:
            raise IOError("Attempted to write a file meant for reading.")
        return self.f.write(s)



class WikiEngine(Engine):
    def __enter__ (self):
        return create_engine(self.url, echo=True)

    def __exit__(self):
        self.dispose()

class Wiki:
    """
        Do not use the class directly. Use open_wiki and new_wiki instead
    """

    def __engine(self):
        return create_engine(f"duckdb:///{self.db_loc.as_posix()}", echo=True)
    def __init__(self, path_dir: pathlib.Path, session: Session, settings: Settings):
        self.__wikistate = WikiState(
            cur_session=session,
            prev_settings=dataclasses.replace(settings),
            cur_settings=dataclasses.replace(settings),
            path_dir=path_dir
        )

        self.db_loc = self.__wikistate.path_dir / NAME_OF_DB_FILE
        GlobalLock().lock()
        # with self.__engine() as e:
        #     WikiBase.metadata.create_all(self.__engine)

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
                    create_empty_file(path)

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


    def open_wikifile(self, item: pathlib.Path, mode: WikiFileMode) -> WikiFile:
        return WikiFile(self.get_wiki_proper_path() / item, mode)
    
    def fetch_items_from_source(self):
        pass

    def is_file(self, item: pathlib.Path):
        return (self.get_wiki_proper_path() / item).is_file()

    def get_wiki_state(self):
        return self.__wikistate

def open_wiki(path_to_wiki_pwi_file: pathlib.Path) -> Wiki:

    """
        Open a wiki and return a Wiki object.
    """

    if not path_to_wiki_pwi_file.exists():
        raise FileNotFoundError(f"{path_to_wiki_pwi_file.as_posix()} doesn't exist")

    session_path = path_to_wiki_pwi_file.parent / ".pw" / "session.json"

    @safe
    def __open_wiki() -> Session:
        with open(session_path, encoding=WIKI_ENCODING) as session_file:
            session_json = json.load(session_file)
            return Session(
                cur_item=session_json["currentFile"]
            )
    
    match __open_wiki():
        case Success(s):
            session = s
        case Failure(FileNotFoundError()):
            logging.info("Session file %s not found, supplying default session configuration...", session_path)
            session = Session(
                cur_item=None
            )
        case Failure(e):
            raise e
        
    wiki = Wiki(
        path_dir=path_to_wiki_pwi_file.parent,
        session=session, # type: ignore
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
    if not valid_item_name(name):
        raise InvalidNameException("Invalid name.")
    wiki_dir = dir_path / name
    wiki_dir.mkdir()
    (wiki_dir / "assets").mkdir()

    wiki_pwi = wiki_dir / "wiki.pwi"
    create_empty_file(wiki_pwi)

    return open_wiki(wiki_pwi)
