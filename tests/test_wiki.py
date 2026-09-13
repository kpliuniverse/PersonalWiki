
import json
import logging
import pathlib
import shutil
import tempfile
from typing import Callable

import pytest

from src.consts import WIKI_ENCODING
from src.utils.wiki_utils import walk_and_return_folder_item
from src.wiki.wiki import create_wiki, open_wiki
from src.wiki.wiki_items import FileItem, UnnamedFolderItem, UnnamedItem, sort_alphabetically_key


def test_open_path(): 

    wiki_dir = pathlib.Path("end-tests/wikis/basic")
    wiki = open_wiki(wiki_dir / "wiki.pwi")
    with open(wiki_dir / ".pw" / "session.json", "r", encoding=WIKI_ENCODING) as session:
        session_json = json.load(session)
    assert wiki.get_cur_item() == session_json["currentFile"] 
    assert wiki.get_cur_item_abs() == wiki_dir / "proper" / session_json["currentFile"]

    with pytest.raises(FileNotFoundError):
        open_wiki(pathlib.Path("end-tests/wikis/does-not-exist/wiki.pwi"))

def test_create_wiki(tmp_path: pathlib.Path):
    temp_end_tests = tmp_path / "end-tests"
    shutil.copytree("end-tests", temp_end_tests)

    temp_wikis = temp_end_tests / "wikis"

    # To generate a folder name
    with tempfile.NamedTemporaryFile(dir=temp_wikis, delete_on_close=True) as t:
        gen_file_path = pathlib.Path(t.name)
        logging.info("Generated throwaway %s", gen_file_path.as_posix())
    if gen_file_path.exists():
        raise FileExistsError("Throwaway file not deleted")

    wiki = create_wiki(gen_file_path.parent, gen_file_path.name)
    assert gen_file_path.is_dir()
    assert (gen_file_path / "proper").is_dir()
    assert (gen_file_path / "wiki.pwi").is_file()


class TestFilterOutEmptyFolders:

    def test_basic(self):
        # Test empty e
        root = UnnamedFolderItem("root")
        x = UnnamedFolderItem("a")
        x.add_child(FileItem("b"))
        root.add_child(x)
        x = UnnamedFolderItem("c")
        x.add_child(FileItem("d"))
        root.add_child(x)
        root.add_child(UnnamedFolderItem("e"))
        inp = root

        root = UnnamedFolderItem("root")
        x = UnnamedFolderItem("a")
        x.add_child(FileItem("b"))
        root.add_child(x)
        x = UnnamedFolderItem("c")
        x.add_child(FileItem("d"))
        root.add_child(x)
        exp_result = root

        assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key).to_str_list() == exp_result.to_str_list()

    def test_empty(self):
        root = UnnamedFolderItem("root")
        x = UnnamedFolderItem("a")
        root.add_child(x)
        x = UnnamedFolderItem("c")
        root.add_child(x)
        root.add_child(UnnamedFolderItem("e"))
        inp = root

        root = UnnamedFolderItem("root")
        exp_result = root

        assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key).to_str_list() == exp_result.to_str_list()

    def test_nested(self):
        root = UnnamedFolderItem("root")
        x = UnnamedFolderItem("a")
        x.add_child(FileItem("b"))
        root.add_child(x)
        x = UnnamedFolderItem("c")
        x.add_child(FileItem("d"))
        x.add_child(UnnamedFolderItem("e"))
        root.add_child(x)
        inp = root

        root = UnnamedFolderItem("root")
        x = UnnamedFolderItem("a")
        x.add_child(FileItem("b"))
        root.add_child(x)
        x = UnnamedFolderItem("c")
        x.add_child(FileItem("d"))
        root.add_child(x)
        exp_result = root

        assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key).to_str_list() == exp_result.sorted(sort_alphabetically_key).to_str_list()
    

def test_file_filter():
    by_alphabet: Callable[[UnnamedItem], str] = lambda x: x.name()
    # base
    base = walk_and_return_folder_item(pathlib.Path("end-tests/folders/walktest")).sorted(key=by_alphabet)
    
    # True case
    assert base.file_filter(lambda _ : True, filter_empty_folders=False).sorted(key=by_alphabet).to_str_list() == base.to_str_list()
    # False case
    assert base.file_filter(lambda _: False).to_str_list() == ["root"]

