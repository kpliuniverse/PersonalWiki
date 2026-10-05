import pathlib
import re

from src.consts import WIKI_ENCODING
from src.utils.item_validity import is_valid_item_name


# i don't know what type to use without restricting to pathlib.Path
def create_empty_file(path):
    with open(path, "x", encoding=WIKI_ENCODING):
        pass


RAW_FILE_EXTENSIONS = {".pwe"}

WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}


def is_valid_file_name(filename: str):
    filename_stripped = filename.strip()
    return all([
        is_valid_item_name(filename),
        filename_stripped.split(".")[0] not in WINDOWS_RESERVED_NAMES
    ])
