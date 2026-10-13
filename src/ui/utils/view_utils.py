from enum import StrEnum
import pathlib

class ViewType(StrEnum):
    ENTRY = "ENTRY"
    TEST = "TEST"
    BLANK = "BLANK"


__ASSOCIATIONS: dict[str, ViewType] = {
    ".pwe": ViewType.ENTRY,
}

def guess_view_type(path: pathlib.Path) -> ViewType:
    return __ASSOCIATIONS.get(path.suffix, ViewType.TEST)