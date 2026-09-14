import pathlib
import shutil
import tempfile

import pytest
from pytestqt.qtbot import QtBot
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QMainWindow, QWidget

from src.exceptions import GUIException
from src.itemmodels.project_item import ItemInfo
from src.ui.components.project_explorer import ProjectExplorer
from src.ui.components.project_tree import ProjectTree, ProjectTreeArgs

from src.utils.move_info import MoveInfo
from src.utils.path_utils import path_dot
from src.utils.wiki_utils import walk_and_return_folder_item
from src.wiki import wiki
from src.wiki.wiki_items import ItemType, FolderItem

def test_parenting_bug(qtbot: QtBot):
    main_window = QMainWindow()

    parent1 = QWidget(main_window)
    projtree1 = ProjectTree(parent=parent1, tree_args=ProjectTreeArgs(
        dir_only=False
    ))
    assert projtree1.parent() == parent1
    parent2 = QWidget(main_window)
    parent2.setLayout(QHBoxLayout())
    projtree2 = ProjectTree(parent=parent2, tree_args=ProjectTreeArgs(
        dir_only=False
    ))
    assert (layout := parent2.layout()) is not None
    layout.addWidget(projtree2)
    assert projtree2.parent() == parent2
    assert projtree1.parent() == parent1


def test_add_path(qtbot: QtBot,): 
    main_window = QMainWindow()
    tree = ProjectTree(parent=main_window, tree_args=ProjectTreeArgs(
        dir_only=False
    ))
    tree.load_folder(FolderItem("root"))
    tree.add_item(ItemInfo(path=path_dot() / "a", item_type=ItemType.FOLDER))

    with pytest.raises(GUIException, match=f"add an already existing path: {(path_dot() / "a").as_posix()}"):
        tree.add_item(ItemInfo(path=path_dot() / "a", item_type=ItemType.FOLDER))

    tree.add_item(ItemInfo(path=path_dot() / "a" / "b", item_type=ItemType.FILE))

    with pytest.raises(GUIException, match="child on a file-type item"):
        tree.add_item(ItemInfo(path_dot() / "a" / "b" / "c", item_type=ItemType.FILE))

    with pytest.raises(GUIException, match="parent of .* doesn't exist"):
        tree.add_item(ItemInfo(path_dot() / "c" / "d", item_type=ItemType.FILE))
    


# def test_move_to_root(qtbot: QtBot, tmp_path: pathlib.Path):
#     main_window = QMainWindow()
#     tmp_wiki_path = tmp_path / "move_test"
#     shutil.copytree(".testenv/wikis/move_test", tmp_wiki_path)
#     assert tmp_wiki_path.exists()
#     tmp_wiki = wiki.open_wiki(tmp_wiki_path / "wiki.pwi")
#     tree = ProjectExplorer(parent=main_window)
#     tree.item_operation_requested.connect(tmp_wiki.do_operations)
#     tree.load(tmp_wiki_path)
#     tree.test_move_item(move_info=MoveInfo.gen_move_info(
#         src=[pathlib.Path("a/b"), pathlib.Path("a/c")],
#         dst=path_root()
#     ))

    