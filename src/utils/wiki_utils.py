import logging
import os
import pathlib
from typing import Optional

from src.wiki.wiki_items import UnnamedFolderItem, FileItem


def walk_and_return_folder_item(root_path: pathlib.Path):
    root_folder_item = UnnamedFolderItem("root")
    cur_folder_stack = [root_folder_item]
    prev_path: Optional[pathlib.Path] = None
    for (path, _, filenames) in os.walk(root_path):
