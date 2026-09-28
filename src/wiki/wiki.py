from collections import deque
from dataclasses import dataclass
import dataclasses
from enum import IntEnum, StrEnum, auto
from io import TextIOWrapper
import json
import logging
from optparse import make_option
import os
import pathlib
import shutil
from typing import IO, Any, List, Optional
from uuid import uuid4, UUID

from attr import define, field, setters
import attrs
import pendulum
from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, Result, Success, attempt, safe
from sqlalchemy import URL, Connection, Engine, create_engine, func, insert, literal, select, text, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session as ORMSession

from src.consts import WIKI_ENCODING
from src.exceptions import InvalidNameException
from src.multiprocessing.multiprocessing import DatabaseLock
from src.states.wikistate import Session, Settings, WikiState
from src.utils.file_utils import RAW_FILE_EXTENSIONS, create_empty_file
from src.utils.item_validity import valid_item_name
from src.utils.item_actions import Action, CopyAction, MoveAction, DeleteAction, NewItemAction
from src.utils.db_utils import get_directory_uuid_query, get_wikidirectory_query, get_wikifile_query, WikiDatabaseError, pathify_cte, query_directory_uuid, gen_uuid
from src.wiki.datamodel import WikiBase, WikiDirectoryEntry, WikiFileEntryType, WikiFileEntry, ROOT_DIR_UUID, WikiItem
from src.utils.wiki_utils import ensure_get_item, get_dir, get_file, get_item
from src.wiki.wiki_items import ItemType

NAME_OF_DB_FILE = "wiki.db"

class WikiOpMode(StrEnum):
    READ = auto()
    WRITE = auto()
    CREATE = auto()
    OVERWRITE = auto()

    def is_write_mode(self):
        return self not in {WikiOpMode.WRITE, WikiOpMode.CREATE, WikiOpMode.OVERWRITE}

CREATE_POINTER_INCOMPATIBILITY_EXCEPTION = ValueError("You cannot create a pointer file. Use Wiki.import_file or Wiki.write_to_new_wikifile. If you actually want to edit the pointer itself, set `work_with_actual_db_value` to True")

@attrs.frozen
class WikiFileMode:
    """
        `op_mode`: The mode that the wikifile opens,
        `byte_mode`: If it's a pointer file, open the underlying file in byte mode
        `ensured_wikifileentry_type`: If not None, expect a certain type of `WikiFileEntryType` and throw an exception if it doesn't meet expectation
        `work_with_actual_db_value`: Overrides `ensured_wikifileentry_type`. When this opens a pointer type file, read/edit that pointer instead of underlying file.
    """
    op_mode: WikiOpMode
    byte_mode: bool = False
    ensured_wikifileentry_type: Optional[WikiFileEntryType] = None
    work_with_actual_db_value: bool = False
    def __post_init__(self):
        if self.byte_mode and self.ensured_wikifileentry_type == WikiFileEntryType.RAW and self.op_mode.is_write_mode():
            raise ValueError("Raw WIkiFileEntries cannot be written in byte-mode")
        if self.op_mode == WikiOpMode.CREATE and self.ensured_wikifileentry_type == WikiFileEntryType.POINTER and not self.work_with_actual_db_value:
            raise CREATE_POINTER_INCOMPATIBILITY_EXCEPTION

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
            raise WikiDatabaseError("Engine is not initialized yet.")
        return self.__engine

    def connect(self):
        if self.__engine is None:
            raise WikiDatabaseError("Engine is not initialized yet.") 
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

    def __init__(self, wiki_dir: pathlib.Path, path: pathlib.Path, mode: WikiFileMode) :
        # self.__f: Optional[IO[Any]] = None
        self.__path = path
        self.__mode = mode
        self.__engine = WikiEngine(gen_db_url(wiki_dir), read_only=mode == WikiOpMode.READ)
        self.__wiki_dir = wiki_dir
        self.__asset_path = wiki_dir / "assets"
        
    def __enter__(self):
        # self.__f = open(self.__path, mode=self.__mode, encoding=WIKI_ENCODING)
        self.__engine.__enter__()
        return self

    def __exit__(self, *args):
        # if self.__f is not None:
        #     self.__f.close()
        if self.__engine is not None:
            self.__engine.__exit__()

    def debug_pathified(self):
        with self.__engine.connect() as c, ORMSession(c) as session:
            for path in session.execute(select(pathify_cte())).all():
                logging.debug("Pathified entry: %s", path
                              )

    def debug_wikifiles(self):
        with self.__engine.connect() as c, ORMSession(c) as session:
            for file in session.query(WikiFileEntry).all():
                logging.debug(file)

    def read(self):
        if self.__engine is None:
            raise IOError("No database opened")
        if self.__mode.op_mode != WikiOpMode.READ:
            raise IOError("Attempted to read a file meant for writing.  ")

        with self.__engine.connect() as c, ORMSession(c) as session:
            # logging.debug("All wikifiles: %s", session.scalars(select(WikiFileEntry)).all())
            # logging.debug("UUID of parent: %s", str(session.scalars(get_directory_uuid_query(self.__path.parent)).one()))

            # This used to use .map() when it used session.execute().
            result: Maybe[WikiFileEntry] = Maybe.from_optional(get_file(c, self.__path))

            
            match result:
                case Some(r):
                    if self.__mode.work_with_actual_db_value:
                        return r.value
                    if self.__mode.ensured_wikifileentry_type is not None and r.type != self.__mode.ensured_wikifileentry_type:
                        raise WikiDatabaseError(f"Attempted to read a {r.type}-type wikifile when its ensured WikiFileEntry type is {self.__mode.ensured_wikifileentry_type}")
                    if r.type == WikiFileEntryType.POINTER:
                        open_mode = "r"
                        if self.__mode.byte_mode:
                            open_mode += "b"
                        with open(self.__asset_path / r.value, mode=open_mode, encoding=WIKI_ENCODING) as f:
                            return f.read()
                    if r.type == WikiFileEntryType.RAW:
                        if self.__mode.byte_mode:
                            return r.value.encode(WIKI_ENCODING)
                        return r.value
                case Nothing:
                    raise WikiDatabaseError("WikiFile not found")

    def write(self, s: Any):
        """
            Write to a file.

            If mode.ensured_wikifileeentry_type is None, and the WikiFileEntry doesn't exist and is trying to create it, assumes RAW
        """
        if self.__engine is None:
            raise IOError("No database opened")
        if self.__mode.op_mode.is_write_mode():
            raise IOError("Attempted to write a file meant for reading.")

        with self.__engine.connect() as c, ORMSession(c) as session, session.begin():
            item = get_file(c, self.__path)
            if item is not None:
                if self.__mode.op_mode == WikiOpMode.CREATE:
                    raise WikiDatabaseError(f"Tried to create a file '{self.__path.as_posix()}' in Create mode, but that path is taken")
                
                if item.type == WikiFileEntryType.RAW or self.__mode.work_with_actual_db_value:
                    item.value = s
                    item.last_modified = pendulum.now()

                if item.type == WikiFileEntryType.POINTER:
                    open_mode = "w"
                    if self.__mode.byte_mode:
                        open_mode += "b"
                    with open(self.__asset_path / item.value, mode=open_mode, encoding=WIKI_ENCODING) as f:
                        f.write(s)
                
            else:
                if self.__mode.op_mode == WikiOpMode.OVERWRITE:
                    raise WikiDatabaseError(f"Tried to overwrite file '{self.__path.as_posix()} in Overwrite mode, but entry doesn't exist or is not a file")
                dir_uuid = query_directory_uuid(session, self.__path.parent)
                
                if self.__mode.ensured_wikifileentry_type == WikiFileEntryType.POINTER and not self.__mode.work_with_actual_db_value:
                    raise CREATE_POINTER_INCOMPATIBILITY_EXCEPTION
                
                typ = Maybe.from_optional(self.__mode.ensured_wikifileentry_type).value_or(WikiFileEntryType.RAW)
                logging.info("typ=%s", typ)
                session.add(
                    WikiFileEntry(
                        name=self.__path.name,
                        type=typ,
                        value=s,
                        directory_uuid=dir_uuid,
                        uuid=gen_uuid(session, WikiFileEntry)
                    )
                )
            


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

        self.db_url = gen_db_url(self.__wikistate.path_dir)

    def get_wiki_dir_path(self):
        return self.__wikistate.path_dir

    def get_wiki_proper_path(self):
        return self.get_wiki_dir_path() / "proper"

    def __copy_file_to_dir(self, connection: Connection, src_uuid: UUID, dir_uuid: UUID, new_name: Optional[str]=None):
        with ORMSession(connection) as session:
            src_file = session.scalars(select(WikiFileEntry).where(WikiFileEntry.uuid == src_uuid)).one()

            dir_dst = session.scalars(select(WikiDirectoryEntry).where(WikiDirectoryEntry.uuid == dir_uuid)).one_or_none()
            session.add(
                WikiFileEntry(
                    name=Result(new_name).value_or(src_file.name),
                    type=src_file.type,
                    value=src_file.value,
                    directory_uuid=dir_uuid,
                    uuid=gen_uuid(session, WikiFileEntry)
                )
            ) 
            
        # with self.open_wikifile(dest, WikiOpMode.CREATE) as f:
        #                     f.write(wiki_file.value)
    
    def __copy_dir(self, connection: Connection, src_uuid: UUID, dst_uuid: UUID, new_name: Optional[str] = None):

        with ORMSession(connection) as session, session.begin():
            uuid_queue = deque([(src_uuid, dst_uuid)])

            while uuid_queue:
                cur_dir_id, dest_dir_id = uuid_queue.pop()
                cur_dir = session.scalars(select(WikiDirectoryEntry).where(WikiDirectoryEntry.uuid == cur_dir_id)).one()
                cur_child_dirs = session.scalars(select(WikiDirectoryEntry).where(WikiDirectoryEntry.parent_uuid == cur_dir_id))
                cur_child_files = session.scalars(select(WikiFileEntry).where(WikiFileEntry.directory_uuid == cur_dir_id))

                new_dir = WikiDirectoryEntry(
                    name=new_name or cur_dir.name,
                    parent_uuid=dest_dir_id,
                    uuid=gen_uuid(session, WikiDirectoryEntry)
                )
                session.add(new_dir )         

                for dir in cur_child_dirs:
                    uuid_queue.append((dir.uuid, new_dir.uuid))

                for file in cur_child_files:
                    self.__copy_file_to_dir(connection, file.uuid, new_dir.uuid)


    def __copy_item_to_dir(self, connection: Connection, item: WikiItem, dir: WikiDirectoryEntry, new_name: Optional[str] = None):
        if isinstance(item, WikiFileEntry):
            self.__copy_file_to_dir(connection, item.uuid, dir.uuid, new_name)
        elif isinstance(item, WikiDirectoryEntry):
            self.__copy_dir(connection, item.uuid, dir.uuid, new_name)
            
    def do_operations(self, actions: List[Action]):
        """
            Given a list of actions, do move, copy, delete,
        """
        
        match actions:
            case []:
                return
            case [MoveAction(src, dst)]:
                
                with WikiEngine(self.db_url) as e, e.connect() as c, ORMSession(c) as session, session.begin():
                    src_item = ensure_get_item(c, src)
                    dst_item = get_item(c, dst)

                    if dst_item is None:
                        dst_parent_item = self.get_dir(dst.parent)
                        if dst_parent_item is None:
                            raise WikiDatabaseError(f"path '{dst.parent}' not found")
                        src_item.change_parent(dst_parent_item.uuid)
                        src_item.rename(dst.name)
                    elif isinstance(dst_item, WikiDirectoryEntry):
                        if isinstance(src_item, WikiDirectoryEntry):
                            src_item.parent_uuid = dst_item.uuid
                        else:
                            src_item.directory_uuid = dst_item.uuid
                    elif isinstance(dst_item, WikiFileEntry):
                        if isinstance(src_item, WikiDirectoryEntry):
                            raise WikiDatabaseError(f"Cannot move directory '{src.as_posix()} to a file '{dst.as_posix()}'")
                        session.delete(src_item)
                        dst_item.copy_from(src_item, copy_uuid=True)
                             
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
                with WikiEngine(self.db_url) as e, e.connect() as c:
                    src_item = ensure_get_item(c, src)
                    dst_item = get_item(c, src)
                    

                    if dst_item is None:
                        dst_parent_item = self.get_dir(dst.parent)
                        if dst_parent_item is None:
                            raise WikiDatabaseError(f"path '{dst.parent}' not found")
                        self.__copy_item_to_dir(c, src_item, dst_parent_item, dst.name)
                    elif isinstance(dst_item, WikiDirectoryEntry):
                        self.__copy_item_to_dir(c, src_item, dst_item)
                    elif isinstance(dst_item, WikiFileEntry):
                        if isinstance(src_item, WikiDirectoryEntry):
                            raise WikiDatabaseError(f"Cannot copy directory '{src.as_posix()} to a file '{dst.as_posix()}'")
                        dst_item.copy_from(src_item, copy_uuid=False)
                    
                    
                # shutil.copy(self.get_wiki_proper_path() / src, self.get_wiki_proper_path() / dst)
            case [DeleteAction(target)]:
                logging.debug("Deleting %s", target)
        
                with WikiEngine(self.db_url) as e, e.connect() as c, ORMSession(c) as session, session.begin(): 
                    if (item := session.scalars(get_wikifile_query(target)).one_or_none()) or (item := session.scalars(get_wikidirectory_query(target)).one_or_none()):
                        session.delete(item)
                        return
                    
                raise WikiDatabaseError(f"Item '{target}' not found")
                # if target.is_file():
                #     os.remove(target)
                # if target.is_dir():
                #     shutil.rmtree(self.get_wiki_proper_path() / target)
            case [NewItemAction(target, create_dir)]:
                if create_dir:
                    logging.debug("Creating item dir %s", target)
                else:
                    logging.debug("Creating item %s", target)
                path = self.get_wiki_proper_path() / target
                if create_dir:
                    with DatabaseLock().lock():
                        self.mkdir(target)                    
                else:
                    with DatabaseLock().lock(), self.open_wikifile(target, WikiFileMode(
                        op_mode=WikiOpMode.CREATE,
                        byte_mode=False,
                        ensured_wikifileentry_type=WikiFileEntryType.RAW
                    )) as f:
                        f.write("")

    def mkdir(self, path: pathlib.Path):        
        with WikiEngine(self.db_url) as e, e.connect() as c, ORMSession(c) as session, session.begin(): 
            session.add(
                WikiDirectoryEntry(
                    name=path.name,
                    parent_uuid=session.scalars(get_directory_uuid_query(path.parent)).one(),
                    uuid=gen_uuid(session, WikiDirectoryEntry)
                )
            )
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


    def open_wikifile(self, item: pathlib.Path, file_mode: WikiFileMode) -> WikiFile:
        # file_mode = WikiFileMode(
        #     op_mode=mode,
        #     byte_mode=False
        # )
        return WikiFile(self.get_wiki_dir_path(), item, file_mode)
    
    def fetch_items_from_source(self):
        pass

    def get_file(self, item: pathlib.Path):
        with WikiEngine(self.db_url).connect() as c:
            return get_file(c, item)

    def get_dir(self, item: pathlib.Path):
        with WikiEngine(self.db_url).connect() as c:
            return get_dir(c, item)
        
    def is_file(self, item: pathlib.Path):
        return self.get_file(item) is not None
    
    def is_dir(self, item: pathlib.Path):
        return self.get_dir(item) is not None
    
    def type_of(self, item: pathlib.Path) -> Optional[ItemType]:
        """
            Returns the type of item a path is. Returns None if it doesn't exist
        """
        if self.is_file(item):
            return ItemType.FILE
        if self.is_dir(item):
            return ItemType.DIRECTORY
        return None
    
    def get_wiki_state(self):
        return self.__wikistate

    # def import_file(self, file: pathlib.Path, dst_file: pathlib.Path):
    #     if file.suffix in RAW_FILE_EXTENSIONS:
    #         with open(file, "r", encoding=WIKI_ENCODING) as f, self.open_wikifile(dst_file, WikiOpMode.CREATE) as w:
    #             w.write(f.read())
    #     else:
    #         with open(file, "rb"), self.open_wikifile(ds)
            

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



    with DatabaseLock().lock(), WikiEngine(gen_db_url(wiki_dir)) as e, e.connect() as c, c.begin():
        WikiBase.metadata.create_all(c)

        with ORMSession(c) as session, session.begin():
            session.add(WikiDirectoryEntry(
                name="root",
                uuid=ROOT_DIR_UUID,
                parent_uuid=None
            ))

            
    return open_wiki(wiki_pwi)
