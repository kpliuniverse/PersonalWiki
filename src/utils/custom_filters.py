
from src.consts import RESOURCE_PATH


def res_path(path: str) -> str:
    """
        Folders `path` to the resource path
    """
    return (RESOURCE_PATH / path).as_uri()