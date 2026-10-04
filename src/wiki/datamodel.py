from datetime import datetime
from enum import Enum
import pathlib
from typing import Optional, Protocol
from uuid import UUID

import pendulum
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import CheckConstraint, Connection, DateTime, ForeignKey, String, event, func, literal, select
from sqlalchemy import Uuid
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, Mapper, mapped_column, relationship
from pydantic_extra_types.pendulum_dt import DateTime as pd_DateTime
from src.exceptions import WikiDatabaseError
from src.utils.item_validity import is_valid_item_name


ROOT_DIR_UUID = UUID(int=0)
class WikiBase(MappedAsDataclass, DeclarativeBase):
    pass


class WikiFileEntryType(Enum):
    RAW = "raw"
    POINTER = "pointer"


    
class WikiItem(Protocol):
    name: Mapped[str]
    uuid: Mapped[UUID]

    def change_parent(self, parent_uuid: UUID): ... 

    def rename(self, new_name: str): ...


class WikiItemModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    uuid: UUID

    @field_validator("name", mode="after")
    @classmethod
    def validate_name(cls, name: str):
        if is_valid_item_name(name):
            raise ValueError(f"'{name}' is not a valid item name.")
class WikiDirectoryEntryModel(WikiItemModel):
    
    parent_uuid: Optional[UUID]

class WikiDirectoryEntry(WikiBase):
    __tablename__ = "wiki_dirs"


    name: Mapped[str] = mapped_column(String(), autoincrement=False)
    uuid: Mapped[UUID] = mapped_column(Uuid(), primary_key=True)
    parent_uuid: Mapped[Optional[UUID]] = mapped_column(ForeignKey(f"{__tablename__}.uuid"), nullable=True) #null = root

    __table_args__ = (
        UniqueConstraint("name", "parent_uuid"),
    )

    def change_parent(self, parent_uuid: UUID):
        self.parent_uuid = parent_uuid

    def rename(self, new_name):
        self.name = new_name

    def __post_init__(self):
        WikiDirectoryEntryModel.model_validate(self)
        # super().__post_init__()



class WikiFileEntryModel(WikiItemModel):
    type: WikiFileEntryType
    value: str
    directory_uuid: UUID
    last_modified: pd_DateTime #pendulum.DateTime has no pydantic schema.

    

class WikiFileEntry(WikiBase):
    __tablename__ = "wiki_files"
    name: Mapped[str] = mapped_column(String())
    type: Mapped[WikiFileEntryType]
    value: Mapped[str]
    uuid: Mapped[UUID] = mapped_column(Uuid(), primary_key=True)
    directory_uuid: Mapped[UUID] = mapped_column(ForeignKey(WikiDirectoryEntry.uuid), nullable=True, default=ROOT_DIR_UUID)
    last_modified: Mapped[pendulum.DateTime] = mapped_column(DateTime(timezone=True), default_factory=pendulum.now)

    __table_args__ = (
        UniqueConstraint("name", "directory_uuid"),
    )

    def __post_init__(self):
        WikiFileEntryModel.model_validate(self)

    def change_parent(self, parent_uuid: UUID):
        self.directory_uuid = parent_uuid

    def copy_from(self, file: WikiFileEntry, copy_uuid=False):
        """
            `file`: the entry to copy from
            `copy_uuid`: copy the `file1 uuid, since uuid's are supposed to be unique, only use it on move
        """
        self.type = file.type
        self.value = file.value
        if copy_uuid:
            self.uuid = file.uuid
        self.last_modified = file.last_modified

    def rename(self, new_name):
        self.name = new_name

@event.listens_for(WikiDirectoryEntry, "after_insert")
def validate_wikidirectoryentry(mapper: Mapper, connection: Connection, target: WikiDirectoryEntry):
    if target.uuid != ROOT_DIR_UUID and target.parent_uuid is None:
        raise WikiDatabaseError("Parent uuid should not be null except for root directory")
    
    if connection.scalar(select(WikiFileEntry).where(WikiFileEntry.directory_uuid == target.parent_uuid).where(WikiFileEntry.name == target.name)):
        raise WikiDatabaseError(f"name '{target.name}' and parent/directory uuid '{target.parent_uuid}' already exists as a file/directory. (Attempted to insert WikiDirectoryEntry that collides with WikiFileEntry)")


@event.listens_for(WikiFileEntry, "after_insert")
def validate_wikifileentry(mapper: Mapper, connection: Connection, target: WikiFileEntry):
    if connection.scalar(select(WikiDirectoryEntry).where(WikiDirectoryEntry.parent_uuid == target.directory_uuid).where(WikiDirectoryEntry.name == target.name)):
        raise WikiDatabaseError(f"name '{target.name}' and parent/directory uuid '{target.directory_uuid}' already exists as a file/directory. (Attempted to insert WikiFileEntry that collides with WikiDirectoryEntry)")

