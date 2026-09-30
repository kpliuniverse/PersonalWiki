
import json
import logging
import pathlib
import shutil
import tempfile
from typing import Callable

import pytest

from src.consts import WIKI_ENCODING
from src.utils.db_utils import WikiDatabaseError
from src.utils.wiki_utils import walk_and_return_folder_item, walk_db_and_return_folder_item
from src.wiki.wiki import create_wiki, open_wiki, WikiFileMode, WikiOpMode, WikiFileEntryType
from src.wiki.wiki_items import FileItem, FolderItem, Item, sort_alphabetically_key
from tests.utils.item_utils import create_folderitem_from_items
from tests.utils.path_utils import gen_available_name
from tests.utils.wiki_utils import create_test_wiki_from_root_folder_item

def test_open_wiki(): 

        wiki_dir = pathlib.Path(".testenv/wikis/basic")
        wiki = open_wiki(wiki_dir / "wiki.pwi")
        with open(wiki_dir / ".pw" / "session.json", "r", encoding=WIKI_ENCODING) as session:
            session_json = json.load(session)
        assert wiki.get_cur_item() == session_json["currentFile"] 
        assert wiki.get_cur_item_abs() == wiki_dir / "proper" / session_json["currentFile"]

        with pytest.raises(FileNotFoundError):
            open_wiki(pathlib.Path("end-tests/wikis/does-not-exist/wiki.pwi"))


def test_create_wiki(tmp_path: pathlib.Path):
    temp_end_tests = tmp_path / "end-tests"
    temp_wikis = temp_end_tests / "wikis"
    temp_wikis.mkdir(parents=True)
    # To generate a folder name
    gen_path_name = gen_available_name(temp_wikis)
    gen_wiki_path = temp_wikis / gen_path_name
    wiki = create_wiki(temp_wikis, gen_path_name)
    assert gen_wiki_path.is_dir()
    assert (gen_wiki_path / "assets").is_dir()
    assert (gen_wiki_path / "wiki.pwi").is_file()


class TestFilterOutEmptyFolders:

    def test_basic(self):
        # Test empty e
        root = FolderItem("root")
        x = FolderItem("a")
        x.add_child(FileItem("b"))
        root.add_child(x)
        x = FolderItem("c")
        x.add_child(FileItem("d"))
        root.add_child(x)
        root.add_child(FolderItem("e"))
        inp = root

        root = FolderItem("root")
        x = FolderItem("a")
        x.add_child(FileItem("b"))
        root.add_child(x)
        x = FolderItem("c")
        x.add_child(FileItem("d"))
        root.add_child(x)
        exp_result = root

        assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key).to_str_list() == exp_result.to_str_list()

    def test_empty(self):
        root = FolderItem("root")
        x = FolderItem("a")
        root.add_child(x)
        x = FolderItem("c")
        root.add_child(x)
        root.add_child(FolderItem("e"))
        inp = root

        root = FolderItem("root")
        exp_result = root

        assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key).to_str_list() == exp_result.to_str_list()

    def test_nested(self):
        root = FolderItem("root")
        x = FolderItem("a")
        x.add_child(FileItem("b"))
        root.add_child(x)
        x = FolderItem("c")
        x.add_child(FileItem("d"))
        x.add_child(FolderItem("e"))
        root.add_child(x)
        inp = root

        root = FolderItem("root")
        x = FolderItem("a")
        x.add_child(FileItem("b"))
        root.add_child(x)
        x = FolderItem("c")
        x.add_child(FileItem("d"))
        root.add_child(x)
        exp_result = root

        assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key).to_str_list() == exp_result.sorted(sort_alphabetically_key).to_str_list()
    

def test_file_filter():
    by_alphabet: Callable[[Item], str] = lambda x: x.name()
    # base
    base = walk_and_return_folder_item(pathlib.Path("end-tests/folders/walktest")).sorted(key=by_alphabet)
    
    # True case
    assert base.file_filter(lambda _ : True, filter_empty_folders=False).sorted(key=by_alphabet).to_str_list() == base.to_str_list()
    # False case
    assert base.file_filter(lambda _: False).to_str_list() == ["root"]


def test_create_folderitem_from_items():
    created = create_folderitem_from_items(
        "root",
        FileItem("a"),
        FileItem("b"),
        create_folderitem_from_items(
            "c",
            FileItem("d"),
            create_folderitem_from_items(
                "e",
                FileItem("f"),
                FileItem("g"),
                create_folderitem_from_items("empty")
            ),
            FileItem("h")
        ),
        FileItem("i")
    )

    compare_root = FolderItem("root")
    compare_root.add_child(FileItem("a"))
    compare_root.add_child(FileItem("b"))

    def folder_c():
        folder_c = FolderItem("c")
        folder_c.add_child(FileItem("d"))

        def folder_e():       
            folder_e = FolderItem("e")
            folder_e.add_child(FileItem("f"))
            folder_e.add_child(FileItem("g"))
            folder_e.add_child(FolderItem("empty"))
            return folder_e

        folder_c.add_child(folder_e())
        folder_c.add_child(FileItem("h"))
        return folder_c

    compare_root.add_child(folder_c())
    compare_root.add_child(FileItem("i"))

    assert created.to_str_list() == compare_root.to_str_list()
    # assert created == compare_root

def test_create_test_wiki_from_root_folder_item_and_walk(tmp_path: pathlib.Path):
    created = create_folderitem_from_items(
        "root",
        FileItem("a"),
        FileItem("b"),
        create_folderitem_from_items(
            "c",
            FileItem("d"),
            create_folderitem_from_items(
                "e",
                FileItem("f"),
                FileItem("g")
            ),
            FileItem("h")
        ),
        FileItem("i")
    )
    
    wiki = create_test_wiki_from_root_folder_item(tmp_path, created)

    # with wiki.get_connection() as c:
    #     result = walk_db_and_return_folder_item(c)
    
    # assert result.to_str_list() == created.to_str_list()


class TestWikiFunctions:

    def __create_test_wiki(self, path: pathlib.Path):
        wiki_name = "test" 
        wiki_path = path / wiki_name
        wiki = create_wiki(path, wiki_name) 
        return (wiki, wiki_path)
    
    def test_create_item(self, tmp_path: pathlib.Path):

        wiki, wiki_path = self.__create_test_wiki(tmp_path)
        
        file1_path = pathlib.Path("file1")
        with wiki.open_wikifile(file1_path, WikiFileMode(
            op_mode=WikiOpMode.CREATE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            f.write("Hello world!")


        with wiki.open_wikifile(file1_path, WikiFileMode(
            op_mode=WikiOpMode.READ,
            byte_mode=False, 
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            assert f.read() == "Hello world!"
            # f.debug_pathified()
        
        with pytest.raises(
            WikiDatabaseError,
            match=f"Tried to create a file '{file1_path.as_posix()}' in Create mode, but that path is taken"
        ), wiki.open_wikifile(file1_path, WikiFileMode(
            op_mode=WikiOpMode.CREATE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            f.write("This should error")
            # f.debug_wikifiles()

        file2_path = pathlib.Path("folder1/file2")

        nonexistent_overwrite_path = pathlib.Path("nonexistent_overwrite")
        with pytest.raises(
            WikiDatabaseError,
            match=f"Tried to overwrite file '{nonexistent_overwrite_path.as_posix()} in Overwrite mode, but entry doesn't exist or is not a file"
        ), wiki.open_wikifile(nonexistent_overwrite_path, WikiFileMode(
            op_mode=WikiOpMode.OVERWRITE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            f.write("This should error")
            # f.debug_wikifiles()

        with wiki.open_wikifile(pathlib.Path("write"), WikiFileMode(
            op_mode=WikiOpMode.WRITE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            f.write("This should write.")

            with pytest.raises(IOError, match="Attempted to read a file meant for writing"):
                f.read()
            # f.debug_wikifiles()
        
        with wiki.open_wikifile(pathlib.Path("write"), WikiFileMode(
            op_mode=WikiOpMode.READ,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            assert f.read() == "This should write."

            with pytest.raises(IOError, match="Attempted to write a file meant for reading"):
                f.write("This should error.")

        folder1_path = pathlib.Path("folder1")
        wiki.mkdir(folder1_path)

        with wiki.open_wikifile(file2_path, WikiFileMode(
            op_mode=WikiOpMode.CREATE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            f.write("Hello world!")


        with wiki.open_wikifile(file2_path, WikiFileMode(
            op_mode=WikiOpMode.READ,
            byte_mode=False, 
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            assert f.read() == "Hello world!"
            # f.debug_pathified()
        
        with pytest.raises(WikiDatabaseError, match=f"Tried to create a file '{file2_path.as_posix()}' in Create mode, but that path is taken"), wiki.open_wikifile(file2_path, WikiFileMode(
            op_mode=WikiOpMode.CREATE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            f.write("This should error")
            f.debug_wikifiles()

        
    # def test_walk_db_and_return_folder_item(self, tmp_path: pathlib.Path):
    #             wiki_name = "test" 
    #     wiki_path = tmp_path / wiki_name
    #     wiki = create_wiki(tmp_path, wiki_name) 

    

            

        
