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
from sqlalchemy import URL, Engine, create_engine

from src.consts import WIKI_ENCODING
from src.exceptions import DataIntegrityError, InvalidNameException, WikiOperationError
from src.multiprocessing.multiprocessing import DatabaseLock
from src.states.wikistate import Session, Settings, WikiState
from src.utils.file_utils import create_empty_file
from src.utils.item_validity import valid_item_name
from src.utils.item_actions import Action, CopyAction, MoveAction, DeleteAction, NewItemAction
from src.wiki.datamodel import WikiBase


NAME_OF_DB_FILE = "wiki.db"

def item_type_mismatch_exception(_src, _dst) -> WikiOperationError:
    return WikiOperationError(f"Cannot move/copy directory/file '{_src.as_posix()}' to a file/directory '{_dst.as_posix()}'")

class DuplicateException(BaseException):
    pass

class WikiOpMode(StrEnum):
    READ = auto()
    WRITE = auto()
    CREATE = auto()
    OVERWRITE = auto()

class DatabaseError(BaseException):
    pass

class WikiEngine():
    """
        Do not use WikiFile directly, except as an argument to WikiFile. Instead use a context manager
    """
    def __init__(self, url: str, read_only: bool = False):
        self.__url = url
        self.__read_only = read_only
        self.__engine: Optional[Engine] = None

    def engine(self):
        if self.__engine is None:
            raise DatabaseError("Engine is not initialized yet.")
        return self.__engine

    def connect(self):
        if self.__engine is None:
            raise DatabaseError("Engine is not initialized yet.") 
        return self.__engine.connect()
    
    def __enter__ (self):
        self.__engine: Optional[Engine] = create_engine(self.__url, echo=True, connect_args={
            "read_only": self.__read_only
        })
        return create_engine(self.__url, echo=True)

    def __exit__(self, *args):
        if self.__engine is not None:
            self.__engine.dispose()

class WikiFile:
    """
        Do not use WikiFile directly. Instead use a context manager.
    """

    def __init__(self, path: pathlib.Path, mode: WikiFileMode, engine: WikiEngine):
        self.__f: Optional[IO[Any]] = None
        self.__path = path
        self.__mode = mode
        self.__engine = engine

    
    def __enter__(self):
        self.__f = open(self.__path, mode=self.__mode, encoding=WIKI_ENCODING)
        self.__engine.__enter__()
        return self

    def __exit__(self, *args):
        if self.__f is not None:
            self.__f.close()
        if self.__engine is not None:
            self.__engine.__exit__()
    
    def read(self):
        if self.__f is None or self.__engine is None:
            raise IOError("No file or database opened")
        if self.__mode != WikiFileMode.READ:
            raise IOError("Attempted to read a file meant for writing.")
        return self.__f.read()

    def write(self, s: Any):
        if self.__f is None:
            raise IOError("No file opened")
        if self.__mode != WikiFileMode.WRITE:
            raise IOError("Attempted to write a file meant for reading.")
        return self.__f.write(s)


def gen_db_url(path_dir: pathlib.Path):
    db_loc = path_dir / NAME_OF_DB_FILE
    return f"duckdb:///{db_loc.as_posix()}"

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

        self.db_loc = gen_db_url(self.__wikistate.path_dir)
        # with self.__engine() as e:
        #     WikiBase.metadata.create_all(self.__engine)

    def get_wiki_dir_path(self):
        return self.__wikistate.path_dir

    def get_wiki_proper_path(self):
        return self.get_wiki_dir_path() / "proper"

    def __copy_file_to_dir(self, session: ORMSession, src_uuid: UUID, dir_uuid: UUID, new_name: Optional[str]=None) -> None:
        src_file: WikiFileEntry = session.get_one(WikiFileEntry, src_uuid)
        dst_name = Maybe.from_optional(new_name).value_or(src_file.name)
        target_dir = session.get(WikiDirectoryEntry, dir_uuid)

        if target_dir is None:
            raise WikiDatabaseError(f"Directory uuid {dir_uuid} not found.")

        #dir_dst = session.scalars(select(WikiDirectoryEntry).where(WikiDirectoryEntry.uuid == dir_uuid)).one_or_none()
        
        if (x := session.query(WikiFileEntry).where(WikiFileEntry.directory_uuid == dir_uuid).where(WikiFileEntry.name == dst_name).one_or_none()) is not None:
            logging.debug("Duplicate detected, overwriting.")
            x.copy_from(src_file)
        else:
                
            session.add(
                WikiFileEntry(
                    name=dst_name,
                    type=src_file.type,
                    value=src_file.value,
                    directory=target_dir,
                    uuid=gen_uuid(session, WikiFileEntry)
                )
            ) 
            
        # with self.open_wikifile(dest, WikiOpMode.CREATE) as f:
        #                     f.write(wiki_file.value)
    
    def __copy_dir(self, session: ORMSession, src_uuid: UUID, dst_uuid: UUID, new_name: Optional[str] = None) -> None:

        uuid_queue: deque[tuple[UUID, UUID]] = deque([(src_uuid, dst_uuid)])
        
        while uuid_queue:
            cur_dir_id, dest_dir_id = uuid_queue.pop()
            cur_dir: WikiDirectoryEntry = session.scalars(select(WikiDirectoryEntry).where(WikiDirectoryEntry.uuid == cur_dir_id)).one()
            cur_child_dirs: List[WikiDirectoryEntry] = cur_dir.dir_children
            cur_child_files: List[WikiFileEntry] = cur_dir.file_children
            
            dest_name = Maybe.from_optional(new_name).value_or(cur_dir.name)

            if (dest_dir := session.query(WikiDirectoryEntry).where(WikiDirectoryEntry.name == dest_name).where(WikiDirectoryEntry.parent_uuid == dest_dir_id).one_or_none()) is None:
                dest_dir = WikiDirectoryEntry(
                    name=new_name or cur_dir.name,
                    parent=session.get(WikiDirectoryEntry, dest_dir_id),
                    uuid=gen_uuid(session, WikiDirectoryEntry)
                )

                session.add(dest_dir)

            for dir in cur_child_dirs:
                uuid_queue.append((dir.uuid, dest_dir.uuid))

            for file in cur_child_files:
                self.__copy_file_to_dir(session, file.uuid, dest_dir.uuid)


    def __copy_item_to_dir(self, session: ORMSession, item: WikiItem, directory: WikiDirectoryEntry, new_name: Optional[str] = None) -> None:
        if isinstance(item, WikiFileEntry):
            self.__copy_file_to_dir(session, item.uuid, directory.uuid, new_name)
        elif isinstance(item, WikiDirectoryEntry):
            self.__copy_dir(session, item.uuid, directory.uuid, new_name)



    def do_operations(self, actions: List[Action]) -> None:
        """
            Given a list of actions, do move, copy, delete,
        """

        
        match actions:
            case []:
                return
            case [MoveAction(src, dst)]:
                logging.info("Moving %s ---> %s", src.as_posix(), dst.as_posix())
                with WikiEngine(self.__db_url) as e, e.connect() as c:
                    with ORMSession(c) as session, session.begin():
                        src_item: WikiFileEntry | WikiDirectoryEntry = ensure_get_item_sess(session, src)
                        dst_item: WikiFileEntry | WikiDirectoryEntry | None = get_item_sess(session, dst)

                        if dst_item is None:
                            dst_parent_item: WikiDirectoryEntry | None = self.get_dir(dst.parent)
                            if dst_parent_item is None:
                                raise WikiOperationError(f"path '{dst.parent}' not found")
                            src_item.change_parent(dst_parent_item.uuid)
                            src_item.rename(dst.name)
                        elif isinstance(dst_item, WikiDirectoryEntry):
                            dst_child: pathlib.Path = dst / src.name
                            existing_child: WikiFileEntry | WikiDirectoryEntry | None = get_item_sess(session, dst_child)

                            if existing_child:
                                logging.info("While moving from %s to directory %s, dest child [dst]/%s detected", src.as_posix(), dst.as_posix(), src.name)
                            if isinstance(src_item, WikiDirectoryEntry):
                                if isinstance(existing_child, WikiFileEntry):
                                    raise item_type_mismatch_exception(src, dst_child)
                                elif isinstance(existing_child, WikiDirectoryEntry):
                                    if iterdir_db_dir_sess(session, dst_child):
                                        raise WikiOperationError(f"Cannot move '{src.as_posix()}' to '{(dst / src.name).as_posix()}', directory not empty")
                                    session.delete(existing_child)
                                    session.flush()
                                src_item.parent_uuid = dst_item.uuid

                            else:
                                if isinstance(existing_child, WikiDirectoryEntry):
                                    raise item_type_mismatch_exception(src, dst_child)
                                if isinstance(existing_child, WikiFileEntry):
                                    session.delete(existing_child)
                                    session.flush()
                                
                                src_item.directory_uuid = dst_item.uuid
                        elif isinstance(dst_item, WikiFileEntry):
                            if isinstance(src_item, WikiDirectoryEntry):
                                raise item_type_mismatch_exception(src, dst)
                            session.delete(src_item)
                            dst_item.copy_from(src_item, copy_uuid=False)
                             
                #     with DatabaseLock().lock(), WikiEngine(self.db_url) as e, e.connect() as c, ORMSession(c) as session, session.begin():
                #         logging.debug("Moving from %s to %s", src.as_posix(), dst.as_posix())
                #         # shutil.move(self.get_wiki_proper_path() / src, self.get_wiki_proper_path() / dst)
                #         wiki_file = src_item
                #         if self.is_dir(dst):
                #             wiki_file.directory_uuid = session.scalars(get_directory_uuid_query(dst)).one().uuid
                #         else:
                #             with self.open_wikifile(dst, WikiFileMode(
                #                 op_mode=WikiOpMode.CREATE,
                #                 byte_mode=False,
                #                 ensured_wikifileentry_type=WikiFileEntryType.RAW
                #             )) as f:
                #                 f.write(wiki_file.value)
                # self.do_operations([DeleteAction(src)])

            case [CopyAction(src, dst)]:
                logging.info("Copying '%s' ---> '%s'", src.as_posix(), dst.as_posix())
                with WikiEngine(self.__db_url) as e, e.connect() as c, ORMSession(c) as session, session.begin():
                    src_item: WikiFileEntry | WikiDirectoryEntry = ensure_get_item_sess(session, src)
                    dst_item: WikiFileEntry | WikiDirectoryEntry | None = get_item_sess(session, dst)
                    

                    if dst_item is None:
                        logging.debug("Destination '%s' doesn't exist, creating...", dst.as_posix())
                        dst_parent_item: WikiDirectoryEntry | None = self.get_dir(dst.parent)
                        if dst_parent_item is None:
                            raise WikiDatabaseError(f"path '{dst.parent}' not found")
                        self.__copy_item_to_dir(session, src_item, dst_parent_item, dst.name)
                    elif isinstance(dst_item, WikiDirectoryEntry):
                        if (x := get_item_sess(session, dst / src.name)) and not (type(x) is type(src_item)):
                            raise item_type_mismatch_exception(src, dst / src.name)
                        self.__copy_item_to_dir(session, src_item, dst_item)        
                    elif isinstance(dst_item, WikiFileEntry):
                        if isinstance(src_item, WikiDirectoryEntry):
                            raise item_type_mismatch_exception(src, dst)
                        dst_item.copy_from(src_item, copy_uuid=False)
                   
                                        
                # shutil.copy(self.get_wiki_proper_path() / src, self.get_wiki_proper_path() / dst)
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

    @safe(exceptions=(NoResultFound,))
    def _mkdir(self, path: pathlib.Path) -> None:

        if path == path_dot():
            raise ValueError("Path points to root")
        if not is_valid_item_name(path.name):
            raise ValueError(f"'{path.name}' is not a valid name")
        
        with WikiEngine(self.__db_url) as e, e.connect() as c, ORMSession(c) as session, session.begin():
            if (parent := get_dir_sess(session, path.parent)) is None:
                raise NoResultFound()
            session.add(
                WikiDirectoryEntry(
                    name=path.name,
                    uuid=gen_uuid(session, WikiDirectoryEntry),
                    parent=parent,
                )
            )

    def mkdir(self, path: pathlib.Path, parents=False) -> None:
        logging.debug("mkdir %s", path.as_posix())
        stack: List[pathlib.Path] = [path]

        while stack:
            cur_path: pathlib.Path = stack[-1]
            result: Result[None, Exception] = self._mkdir(cur_path)

            match result:
                case Success(_):
                    stack.pop()
                case Failure(NoResultFound()):
                    stack.append(cur_path.parent)
                case Failure(e):
                    raise e





    def set_cur_item(self, item: pathlib.Path) -> None:
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
        return WikiFile(self.get_wiki_proper_path() / item, mode, WikiEngine(self.db_url, read_only=mode == WikiFileMode.READ))
    
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


    with GlobalLock().lock():
        with WikiEngine(gen_db_url(wiki_dir)) as e:
            with e.connect() as c:
                WikiBase.metadata.create_all(c)
                c.commit()


    return open_wiki(wiki_pwi)
