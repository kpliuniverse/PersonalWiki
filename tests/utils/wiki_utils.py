import logging
import pathlib

from src.wiki.datamodel import WikiFileEntryType
from src.wiki.wiki import Wiki, WikiFileMode, WikiOpMode
from src.wiki.wiki_items import FolderItem, Item, ItemType


def populate_from_root_folder_item(wiki: Wiki, root_folder: FolderItem):
    flat_list = root_folder.to_flat_list()
    logging.debug("Root item folder flat list:")
    for l in flat_list:
        logging.debug("--%s", l.path.relative_to(root_folder.name()).as_posix())
        
    for l in flat_list:
        
        path = l.path.relative_to(root_folder.name())
        dir_path = path
        
        if l.type == ItemType.FILE:
            dir_path = dir_path.parent

        if not wiki.is_dir(dir_path):
            wiki.mkdir(dir_path, parents=True)

        if l.type == ItemType.FILE:
            with wiki.open_wikifile(pathlib.Path(path), WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )):
                pass
    
            