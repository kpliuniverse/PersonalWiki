
import pathlib
from typing import Any, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import CTE, ScalarSelect, Select, literal, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session as ORMSession
from sqlalchemy.sql.base import ReadOnlyColumnCollection
from sqlalchemy.sql.elements import KeyedColumnElement
from sqlalchemy.sql.selectable import CTE

from src.exceptions import WikiDatabaseError
from src.utils.path_utils import path_dot
from src.wiki.datamodel import (
    ROOT_DIR_UUID,
    ROOT_NAME,
    WikiBase,
    WikiDirectoryEntry,
    WikiFileEntry,
)


class JustUUID:
    uuid: UUID


def pathify_directories_cte() -> CTE[ReadOnlyColumnCollection[str, KeyedColumnElement[Any]]]:
    cte: CTE[ReadOnlyColumnCollection[str, KeyedColumnElement[Any]]] = (
        select(WikiDirectoryEntry.uuid, WikiDirectoryEntry.name.label("path"))
        # .where(WikiDirectoryEntry.parent_uuid.is_(None))
        .cte("directories", recursive=True)
    )

    DirEntryAlias = WikiDirectoryEntry

    cte: CTE[ReadOnlyColumnCollection[str, KeyedColumnElement[Any]]] = cte.union_all(
        select(WikiDirectoryEntry.uuid, cte.c.path + literal("/") + WikiDirectoryEntry.name.label("path"))
        .join(cte, DirEntryAlias.parent_uuid == cte.c.uuid)
    )

    return cte


def get_directory_uuid_query(path: pathlib.Path) -> Select[UUID]:
    """
        Return a query to get the id of a certain path
    """
    # Example: a/b/c


    # directories = text(f"""
    #         SELECT id, name AS path FROM {WikiDirectoryEntry.__tablename__}
    #             WHERE parent_id IS NULL
    #         UNION ALL
    #         SELECT h.id, CONCAT(hp.path, '/', h.name) FROM {WikiDirectoryEntry.__tablename__} h
    #             JOIN hierarchy_paths hp ON h.parent_id = hp.id
    # """).
    cte: CTE[ReadOnlyColumnCollection[str, KeyedColumnElement[Any]]] = pathify_directories_cte()
    return select(cte.c.uuid).where(cte.c.path == (pathlib.Path(ROOT_NAME) / path).as_posix())



def query_directory_uuid(session: ORMSession, path: pathlib.Path) -> UUID:
    if path == path_dot():
        return ROOT_DIR_UUID
    try:
        return session.scalars(get_directory_uuid_query(path)).one()
    except NoResultFound as e:
        raise WikiDatabaseError(f"Directory {path.as_posix} not found") from e




def gen_uuid(session: ORMSession, table: type[WikiDirectoryEntry] | type[WikiFileEntry]) -> UUID:
    while True:
        uuid: UUID = uuid4()
        if uuid == ROOT_DIR_UUID:
            continue
        if len(session.scalars(select(table).where(table.uuid == uuid)).all()) == 0:
            return uuid


