
import json
import logging
import pathlib
import shutil
import tempfile
from typing import Callable

import pytest

from src.consts import WIKI_ENCODING
from src.utils.db_utils import WikiDatabaseError
from src.utils.item_actions import MoveAction
from src.utils.wiki_utils import walk_and_return_folder_item, walk_db_and_return_folder_item
from src.wiki.wiki import Wiki, create_wiki, open_wiki, WikiFileMode, WikiOpMode, WikiFileEntryType
from src.wiki.wiki_items import FileItem, FolderItem, Item, sort_alphabetically_key
from tests.utils.path_utils import gen_available_name
from tests.utils.wiki_utils import populate_from_root_folder_item
from src.wiki.datamodel import ROOT_DIR_UUID

def test_open_wiki(): 

        wiki_dir = pathlib.Path(".testenv/wikis/basic")
        wiki = open_wiki(wiki_dir / "wiki.pwi")
        with open(wiki_dir / ".pw" / "session.json", "r", encoding=WIKI_ENCODING) as session:
            session_json = json.load(session)
        assert wiki.get_cur_item() == session_json["currentFile"] 
        assert wiki.get_cur_item_abs() == wiki_dir / "proper" / session_json["currentFile"]

        with pytest.raises(FileNotFoundError):
            open_wiki(pathlib.Path("end-tests/wikis/does-not-exist/wiki.pwi"))





class TestWikiItem:
    class TestFilterOutEmptyFolders:

        @staticmethod
        def test_basic():
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

            assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key) == exp_result

        @staticmethod
        def test_empty():
            root = FolderItem("root")
            x = FolderItem("a")
            root.add_child(x)
            x = FolderItem("c")
            root.add_child(x)
            root.add_child(FolderItem("e"))
            inp = root

            root = FolderItem("root")
            exp_result = root

            assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key) == exp_result

        @staticmethod
        def test_nested():
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

            assert inp.filter_out_empty_folders().sorted(sort_alphabetically_key) == exp_result.sorted(sort_alphabetically_key)
        

    @staticmethod
    def test_file_filter():
        by_alphabet: Callable[[Item], str] = lambda x: x.name()
        # base
        base = walk_and_return_folder_item(pathlib.Path("end-tests/folders/walktest")).sorted(key=by_alphabet)
        
        # True case
        assert base.file_filter(lambda _ : True, filter_empty_folders=False).sorted(key=by_alphabet) == base
        # False case
        assert base.file_filter(lambda _: False) == FolderItem("root")


    @pytest.mark.dependency()
    @staticmethod
    def test_folderitem_with_child_arguments():

        empty = FolderItem("root")
        assert not empty.children()

        created = FolderItem(
            "root",
            FileItem("a"),
            FileItem("b"),
            FolderItem(
                "c",
                FileItem("d"),
                FolderItem(
                    "e",
                    FileItem("f"),
                    FileItem("g"),
                    FolderItem("empty")
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

        assert created == compare_root
    # assert created == compare_root




class TestWikiFunctions:

    @staticmethod
    @pytest.mark.dependency()
    def test_create_wiki(tmp_path: pathlib.Path):
        gen_path_name = gen_available_name(tmp_path)
        gen_wiki_path = tmp_path / gen_path_name
        wiki = create_wiki(tmp_path, gen_path_name)
        assert gen_wiki_path.is_dir()
        assert (gen_wiki_path / "assets").is_dir()
        assert (gen_wiki_path / "wiki.pwi").is_file()

    @staticmethod
    @pytest.mark.dependency(depends=['TestWikiFunctions::test_create_wiki'])
    def test_create_item(wiki: Wiki):        
        file1_path = pathlib.Path("file1")
        with wiki.open_wikifile(pathlib.Path("blank"), WikiFileMode(
            op_mode=WikiOpMode.CREATE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            pass
        
        assert wiki.is_file(pathlib.Path("blank"))

        with wiki.open_wikifile(file1_path, WikiFileMode(
            op_mode=WikiOpMode.CREATE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            f.write("Hello world!")


        
        assert wiki.is_file(file1_path)
        assert wiki.get_file(file1_path).value == "Hello world!" # type: ignore , already assured by prior assertion of wiki.is_file(file1_path)

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
        assert (d := wiki.get_dir(pathlib.Path("folder1"))) is not None and d.parent_uuid == ROOT_DIR_UUID

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

        parentless_dir = pathlib.Path("folder2/folder3")
        # Test mkdir with parents=True
        wiki.mkdir(parentless_dir, parents=True)
        wiki.is_dir(parentless_dir)

        # Test writing a file that shares a path with a folder and v/v
        error_pat = "name '.*' and parent/directory uuid '.*' already exists as a file/directory. .*"
        with pytest.raises(WikiDatabaseError, match=error_pat), \
            wiki.open_wikifile(folder1_path,
                WikiFileMode(
                    op_mode=WikiOpMode.WRITE,
                    byte_mode=False,
                    ensured_wikifileentry_type=WikiFileEntryType.RAW
                )
            ) as f:
                f.write("This should error")

        with pytest.raises(WikiDatabaseError, match=error_pat):
            wiki.mkdir(pathlib.Path("file1"))
    @staticmethod
    @pytest.mark.dependency(depends=["TestWikiItem::test_folderitem_with_child_arguments", "TestWikiFunctions::test_create_item"])
    def test_populate_from_root_folder_item(wiki: Wiki):
        created = FolderItem(
            "root",
            FileItem("a"),
            FolderItem(
                "c",
                FileItem("d"),
                FolderItem(
                    "e",
                    FileItem("f"),
                    FileItem("g")
                ),
                FileItem("h")
            ),
            FileItem("i")
        )
        
        populate_from_root_folder_item(wiki, created)

        assert wiki.is_file(pathlib.Path("a"))
        assert wiki.is_dir(pathlib.Path("c"))
        assert wiki.is_file(pathlib.Path("c/d"))
        assert wiki.is_dir(pathlib.Path("c/e"))
        assert wiki.is_file(pathlib.Path("c/e/f"))
        assert wiki.is_file(pathlib.Path("c/e/g"))
        assert wiki.is_file(pathlib.Path("c/h"))
        assert wiki.is_file(pathlib.Path("i"))

    @staticmethod
    @pytest.mark.dependency(depends=["TestWikiFunctions::test_populate_from_root_folder_item"])
    def test_wiki_walk(wiki: Wiki):

        created = FolderItem(
            "root",
            FileItem("a"),
            FolderItem(
                "c",
                FileItem("d"),
                FolderItem(
                    "e",
                    FileItem("f"),
                    FileItem("g"),
                    FolderItem("b")
                ),
                FileItem("h")
            ),
            FileItem("i")
        )
        
        populate_from_root_folder_item(wiki, created)

        with wiki.get_engine() as e, e.connect() as c:
            assert walk_db_and_return_folder_item(c).sorted(sort_alphabetically_key) == created.sorted(sort_alphabetically_key)

    class TestMove:

        @staticmethod
        def test_rename(wiki: Wiki):

            with wiki.open_wikifile(pathlib.Path("a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("Hello world")

            with wiki.open_wikifile(pathlib.Path("b"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("This is going to be overwritten")

            wiki.do_operations([
                MoveAction(pathlib.Path("a"), pathlib.Path("a_renamed"))
            ])

            with wiki.open_wikifile(pathlib.Path("a_renamed"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "Hello world"

            wiki.do_operations([
                MoveAction(pathlib.Path("a_renamed"), pathlib.Path("b"))
            ])

            with wiki.open_wikifile(pathlib.Path("b"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "Hello world"

        @staticmethod
        @pytest.mark.dependency(depends=["TestWikiFunctions::test_wiki_walk"])
        def test_move_to_dir_simple(wiki: Wiki):
            populate_from_root_folder_item(wiki, FolderItem("root",
                FileItem("a"),
                FolderItem("b",
                    FileItem("c")
                )
            ))

            wiki.do_operations([
                MoveAction(pathlib.Path("a"), pathlib.Path("b"))
            ])

            result = FolderItem("root", 
                FolderItem("b",
                    FileItem("a"),
                    FileItem("c")
                )
            )

            with wiki.get_engine() as e, e.connect() as c:
                assert walk_db_and_return_folder_item(c).sorted(sort_alphabetically_key) == result.sorted(sort_alphabetically_key)

        @staticmethod
        @pytest.mark.dependency(depends=["TestWikiFunctions::test_wiki_walk"])
        def test_move_to_dir_nested(wiki: Wiki):
            
            moved_folder = FolderItem("a", 
                FileItem("ab"),
                FileItem("ac"),
                FolderItem("ad"),
                FolderItem("ae",
                    FileItem("aea"),
                    FileItem("aeb")   
                )
            )
            populate_from_root_folder_item(wiki, FolderItem("root",
                moved_folder,
                FolderItem("b",
                    FileItem("c"),
                    FolderItem("d")
                )
            ))

            wiki.do_operations([
                MoveAction(pathlib.Path("a"), pathlib.Path("b/d"))
            ])

            result = FolderItem("root", 
                FolderItem("b",
                    FileItem("c"),
                    FolderItem("d", moved_folder)
                )
            )

            with wiki.get_engine() as e, e.connect() as c:
                assert walk_db_and_return_folder_item(c).sorted(sort_alphabetically_key) == result.sorted(sort_alphabetically_key)

        
    # with wiki.get_connection() as c:
    #     result = walk_db_and_return_folder_item(c)
    
    # assert result.to_str_list() == created.to_str_list()
    # def test_walk_db_and_return_folder_item(self, tmp_path: pathlib.Path):
    #             wiki_name = "test" 
    #     wiki_path = tmp_path / wiki_name
    #     wiki = create_wiki(tmp_path, wiki_name) 

    

            

        
