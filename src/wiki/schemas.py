from typing import Optional
from uuid import UUID

from pydantic import ConfigDict


class WikiDirectoryEntryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    uuid: UUID
    parent_uuid: Optional[UUID]


