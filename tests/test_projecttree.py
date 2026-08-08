import pathlib
import tempfile

import pytest
from pytestqt.qtbot import QtBot

from src.exceptions import GUIException
from src.ui.components.project_tree import ProjectTree, ProjectTreeArgs

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QMainWindow, QWidget

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


def test_add_path(qtbot: QtBot, tmp_path: pathlib.Path): 
    main_window = QMainWindow()
    tree = ProjectTree(parent=main_window, tree_args=ProjectTreeArgs(
        dir_only=False
    ))
    tree.load(tmp_path)
    tree.add_item(tmp_path / "a")
    tree.add_item(tmp_path / "a" / "b")
    with pytest.raises(GUIException) as e_info:
        tree.add_item(tmp_path / "c" / "d")