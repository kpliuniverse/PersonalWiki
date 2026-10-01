from PyQt6.QtGui import QIcon

from typing import Dict, List, Set, Tuple

from src.resources import ResourceManager


def __flatten(l: List[Tuple[str | Set[str], str]]) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for item in l:
        cond = item[0]
        value = item[1]
        if isinstance(cond, str):
            cond = {cond}

        for extension in cond:
            if extension in d:
                continue
            d[extension] = value
            
    return d


_ICON_PATH = "icons/48px"

_ICON_DICT = __flatten([

    ({".png", ".jpg", ".jpeg", ".webp", ".bmp"}, "image.png"),
    (".pwe", "document.png"),
])

def _load_icon(path: str) -> QIcon:
    return ResourceManager().assert_get_res(path, assert_type=QIcon)


def get_icon_from_extension(extension: str):
    # Lazy-load icons to avoid QIcon creation at import time
    return _load_icon(f"{_ICON_PATH}/{_ICON_DICT.get(extension, "file.png")}")
