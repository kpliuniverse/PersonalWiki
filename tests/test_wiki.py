
import json
import logging
from pathlib import Path
import shutil
import tempfile
from typing import Callable

from deepdiff import DeepDiff
from deepdiff.helper import COLORED_VIEW
from pydantic import ValidationError
import pytest
from sqlalchemy.orm import Session

from src.consts import WIKI_ENCODING
from src.exceptions import InvalidNameException
from src.utils.db_utils import WikiDatabaseError
from src.utils.item_actions import CopyAction, MoveAction
from src.utils.wiki_utils import walk_and_return_folder_item, walk_db_and_return_folder_item
from src.wiki.wiki import Wiki, create_wiki, open_wiki, WikiFileMode, WikiOpMode, WikiFileEntryType
from src.wiki.wiki_items import FileItem, FolderItem, Item, sort_alphabetically_key
from tests.utils.path_utils import gen_available_name
from tests.utils.wiki_utils import populate_from_root_folder_item
from src.wiki.datamodel import ROOT_DIR_UUID, WikiDirectoryEntry

def test_open_wiki(): 

        wiki_dir = Path(".testenv/wikis/basic")
        wiki = open_wiki(wiki_dir / "wiki.pwi")
        with open(wiki_dir / ".pw" / "session.json", "r", encoding=WIKI_ENCODING) as session:
            session_json = json.load(session)
        assert wiki.get_cur_item() == session_json["currentFile"] 
        assert wiki.get_cur_item_abs() == wiki_dir / "proper" / session_json["currentFile"]

        with pytest.raises(FileNotFoundError):
            open_wiki(Path("end-tests/wikis/does-not-exist/wiki.pwi"))





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
        base = walk_and_return_folder_item(Path("end-tests/folders/walktest")).sorted(key=by_alphabet)
        
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

class TestWikiEngine:

    @staticmethod
    @pytest.mark.dependency()
    def test_invalid_data(wiki: Wiki):
        
        #this should be changed to raise a specialized exception right after we implement data validation
        with pytest.raises(ValidationError), wiki.get_engine() as e, e.connect() as c, Session(c) as session, session.begin():
            session.add(WikiDirectoryEntry(name=3, uuid="hello", parent_uuid=ROOT_DIR_UUID))


class TestWikiFunctions:

    @staticmethod
    def test_create_with_invalid_wiki_name(tmp_path: Path):
        
        invalid_names = [".", ".."]
        for name in invalid_names:
            with pytest.raises(InvalidNameException, match=f"'{name}' is an invalid name"):
                wiki = create_wiki(tmp_path, name)



    @staticmethod
    @pytest.mark.dependency()
    def test_create_wiki(tmp_path: Path):
        gen_path_name = gen_available_name(tmp_path)
        gen_wiki_path = tmp_path / gen_path_name
        wiki = create_wiki(tmp_path, gen_path_name)
        assert gen_wiki_path.is_dir()
        assert (gen_wiki_path / "assets").is_dir()
        assert (gen_wiki_path / "wiki.pwi").is_file()

    @staticmethod
    @pytest.mark.dependency(depends=['TestWikiFunctions::test_create_wiki'])
    def test_create_item(wiki: Wiki):        
        file1_path = Path("file1")
        with wiki.open_wikifile(Path("blank"), WikiFileMode(
            op_mode=WikiOpMode.CREATE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            pass
        
        assert wiki.is_file(Path("blank"))

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

        file2_path = Path("folder1/file2")

        nonexistent_overwrite_path = Path("nonexistent_overwrite")
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

        with wiki.open_wikifile(Path("write"), WikiFileMode(
            op_mode=WikiOpMode.WRITE,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            f.write("This should write.")

            with pytest.raises(IOError, match="Attempted to read a file meant for writing"):
                f.read()
            # f.debug_wikifiles()
        
        with wiki.open_wikifile(Path("write"), WikiFileMode(
            op_mode=WikiOpMode.READ,
            byte_mode=False,
            ensured_wikifileentry_type=WikiFileEntryType.RAW
        )) as f:
            assert f.read() == "This should write."

            with pytest.raises(IOError, match="Attempted to write a file meant for reading"):
                f.write("This should error.")

        folder1_path = Path("folder1")
        wiki.mkdir(folder1_path)
        assert (d := wiki.get_dir(Path("folder1"))) is not None and d.parent_uuid == ROOT_DIR_UUID

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

        parentless_dir = Path("folder2/folder3")
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
            wiki.mkdir(Path("file1"))
            
        # Write on a nonexistentfolder
        with pytest.raises(WikiDatabaseError, match="Directory .* not found"):
            with wiki.open_wikifile(Path("non_existent_folder/a"),
                WikiFileMode(
                    op_mode=WikiOpMode.WRITE,
                    byte_mode=False,
                    ensured_wikifileentry_type=WikiFileEntryType.RAW
                )
            ) as f:
                f.write("This should error")

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

        assert wiki.is_file(Path("a"))
        assert wiki.is_dir(Path("c"))
        assert wiki.is_file(Path("c/d"))
        assert wiki.is_dir(Path("c/e"))
        assert wiki.is_file(Path("c/e/f"))
        assert wiki.is_file(Path("c/e/g"))
        assert wiki.is_file(Path("c/h"))
        assert wiki.is_file(Path("i"))

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

            with wiki.open_wikifile(Path("a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("Hello world")

            with wiki.open_wikifile(Path("b"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("This is going to be overwritten")

            wiki.do_operations([
                MoveAction(Path("a"), Path("a_renamed"))
            ])

            with wiki.open_wikifile(Path("a_renamed"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "Hello world"

            wiki.do_operations([
                MoveAction(Path("a_renamed"), Path("b"))
            ])

            with wiki.open_wikifile(Path("b"), file_mode=WikiFileMode(
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
                MoveAction(Path("a"), Path("b"))
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
            with wiki.open_wikifile(Path("a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("Hello world")

            with wiki.open_wikifile(Path("d/a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("Hello world")
            wiki.do_operations([
                MoveAction(Path("a"), Path("b/d"))
            ])

            result = FolderItem("root", 
                FolderItem("b",
                    FileItem("c"),
                    FolderItem("d", moved_folder)
                )
            )

            
            with wiki.get_engine() as e, e.connect() as c:
                assert walk_db_and_return_folder_item(c).sorted(sort_alphabetically_key) == result.sorted(sort_alphabetically_key)
        
        @staticmethod
        @pytest.mark.dependency(depends=["TestWikiFunctions::test_wiki_walk", "TestWikiFunctions::TestMove::test_rename", "TestWikiFunctions::TestMove::move_to_dir_simple"])
        def test_move_to_dir_override(wiki: Wiki):
            populate_from_root_folder_item(wiki, FolderItem("root",
                FolderItem("b", FileItem("ba")),
                FolderItem("c", FileItem("ca")),
                FolderItem("d",
                    FolderItem("b", FileItem("ba")),
                    FolderItem("c", FileItem("ca")),
                )
            ))

            with wiki.open_wikifile(Path("a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "Hello world"      

            with wiki.open_wikifile(Path("d/a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "This is going to be overwritten"      
            
            wiki.do_operations([
                MoveAction(Path("a"), Path("d"))
            ])


            
            
        @staticmethod
        def test_move_dir_to_dir_override(wiki: Wiki):
            populate_from_root_folder_item(wiki, FolderItem("root",
                FolderItem("a",
                    FolderItem("b",
                        FileItem("c")
                    ),
                )
            ))
        @staticmethod
        @pytest.mark.dependency(depends=["TestWikiFunctions::test_wiki_walk"])
        def test_invalid_move(wiki: Wiki):
            structure = FolderItem("root",
                FolderItem("a"),
                FileItem('b')
            )


            populate_from_root_folder_item(wiki, structure)

            with pytest.raises(WikiDatabaseError, match="Cannot move directory '.*' to a file '.*'"):
                wiki.do_operations(
                    [MoveAction(Path("a"), Path("b"))]
                )
            
    class TestCopy:
        
        @staticmethod
        def test_copy_file_to_nonexistent(wiki: Wiki):
            with wiki.open_wikifile(Path("a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("Hello world.")

            result = FolderItem("root", FileItem("a"), FileItem("b"))
            
            wiki.do_operations([
                CopyAction(Path("a"), Path("b"))
            ])

            with wiki.get_engine() as e, e.connect() as c:
                structure = walk_db_and_return_folder_item(c).sorted(sort_alphabetically_key)
                expected = result.sorted(sort_alphabetically_key)
                assert structure == expected, "\n" + str(DeepDiff(expected.to_str_list(), structure.to_str_list(), view=COLORED_VIEW))

            with wiki.open_wikifile(Path("a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "Hello world."
                
        
            with wiki.open_wikifile(Path("b"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "Hello world."
        
        @staticmethod
        def test_overriding_copy(wiki: Wiki):
            with wiki.open_wikifile(Path("a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("Hello world.")
                
            with wiki.open_wikifile(Path("b"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.CREATE,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                f.write("This is going to be overwritten.")

            result = FolderItem("root", FileItem("a"), FileItem("b"))
            
            with wiki.get_engine() as e, e.connect() as c:
                structure = walk_db_and_return_folder_item(c).sorted(sort_alphabetically_key)
                expected = result.sorted(sort_alphabetically_key)
                assert structure == expected, "\n" + str(DeepDiff(expected.to_str_list(), structure.to_str_list(), view=COLORED_VIEW))

            with wiki.open_wikifile(Path("a"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "Hello world."
                
        
            with wiki.open_wikifile(Path("b"), file_mode=WikiFileMode(
                op_mode=WikiOpMode.READ,
                byte_mode=False,
                ensured_wikifileentry_type=WikiFileEntryType.RAW
            )) as f:
                assert f.read() == "Hello world."
            
        
    # with wiki.get_connection() as c:
    #     result = walk_db_and_return_folder_item(c)
    
    # assert result.to_str_list() == created.to_str_list()
    # def test_walk_db_and_return_folder_item(self, tmp_path: Path):
    #             wiki_name = "test" 
    #     wiki_path = tmp_path / wiki_name
    #     wiki = create_wiki(tmp_path, wiki_name) 

    

            

        
