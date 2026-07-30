
import re


WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}


def valid_wiki_name(filename: str):
    filename_stripped = filename.strip()
    return all([
        filename_stripped != "",
        re.search("[\\\\/&?!<>:\"|?* ]", filename_stripped) is None,
        filename_stripped.split(".")[0] not in WINDOWS_RESERVED_NAMES
    ])
        