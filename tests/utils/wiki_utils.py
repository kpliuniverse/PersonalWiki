import logging
import pathlib

from deepdiff import DeepDiff
from deepdiff.helper import COLORED_VIEW

from src.utils.wiki_utils import walk_db_and_return_folder_item
from src.wiki.datamodel import WikiFileEntryType
from src.wiki.wiki import Wiki, WikiFileMode, WikiOpMode
from src.wiki.wiki_items import FolderItem, Item, ItemType, sort_alphabetically_key


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
    

def assert_same_folder_structure(wiki: Wiki, expected: FolderItem):
    """
        Assert if the wiki matches the expected folder structure. The FolderItem's name must be named 'root'
    """
    
    with wiki.get_engine() as e, e.connect() as c:
        expected = expected.sorted(sort_alphabetically_key)
        result = walk_db_and_return_folder_item(c).sorted(sort_alphabetically_key)
        assert result == expected,  "\n" + str(DeepDiff(expected.to_str_list(), result.to_str_list(), view=COLORED_VIEW))