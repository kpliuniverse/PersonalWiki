from ..src.components.projecttree import ProjectTree, ProjectTreeArgs
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QMainWindow, QWidget


def test_parenting_bug(qtbot):
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
