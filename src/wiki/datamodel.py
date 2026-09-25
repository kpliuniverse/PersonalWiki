from datetime import datetime
from enum import Enum
from typing import Optional

import pendulum
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship

class WikiBase(MappedAsDataclass, DeclarativeBase):
    pass


class WikiEntryType(Enum):
    RAW = "raw"
    POINTER = "pointer"

class WikiDirectoryEntry(WikiBase):
    __tablename__ = "wiki_folders"

    name: Mapped[str] = mapped_column(String(256), primary_key=True)
    parent_uuid: Mapped[Optional[str]] = mapped_column(ForeignKey("wiki_folders.uuid"),primary_key=True) #null = root
    uuid: Mapped[str] = mapped_column(String(36), unique=True)

class WikiFileEntry(WikiBase):
    __tablename__ = "wiki_files"

    name: Mapped[str] = mapped_column(String(256), primary_key=True)
    type: Mapped[WikiEntryType]
    value: Mapped[str]
    last_modified: Mapped[pendulum.DateTime] = mapped_column(DateTime(timezone=True))
    directory_uuid: Mapped[str] = mapped_column(ForeignKey("wiki_folders.uuid"))
