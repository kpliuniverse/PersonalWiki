import logging
import pathlib
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QMenu,
    QWidget,
    QVBoxLayout,
    QToolBar,
    QPushButton, QPlainTextEdit, QHBoxLayout, QLineEdit
)

from src.consts import ITEM_DATA_ROLE
from src.itemmodels.project_item import ItemInfo
from src.ui.dialogs.item_move_dialog import ItemMoveDialog
from src.ui.dialogs.item_rename_dialog import ItemRenameDialog, RenameInfo
from src.ui.stylesheets.app_stylesheet import MainStylesheetManager
from src.utils.item_actions import DeleteAction, MoveAction, NewItemAction
from src.utils.move_info import MoveInfo
from src.ui.dialogs.item_new_dialog import ItemNewDialog
from src.ui.components.project_tree import DragDropInfo, ProjectTree, ProjectTreeArgs
from src.exceptions import GUIException
from src.items.items import ItemCreationResult, ItemRecognizedType
from src.resources import ResourceManager
from src.utils.wiki_utils import walk_and_return_folder_item
from src.wiki.wiki_items import ItemType, sort_alphabetically_key


class SearchToolbar(QToolBar):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container.setLayout(container_layout)
        self.search_input = QLineEdit(parent=self)
        self.search_input.setPlaceholderText("Search")
        container_layout.addWidget(self.search_input)
        # self.search_button = QPushButton("Search", parent=self)
        # container_layout.addWidget(self.search_button)
        self.addWidget(container)

class ProjectExplorerToolbar(QToolBar):
    def __init__(self, parent: QWidget):
        super().__init__(parent)



        res_mgr = ResourceManager()
        self.new_btn = QPushButton(parent=self, text="", icon=res_mgr.get("icons/96px/plus.png").res)
        self.new_btn.setToolTip("New Item")
        self.addWidget(self.new_btn)

        self.move_btn = QPushButton(parent=self, text="", icon=res_mgr.get("icons/96px/move.png").res)
        self.move_btn.setToolTip("Move Items")
        self.addWidget(self.move_btn)

        self.del_btn = QPushButton(parent=self, text="", icon=res_mgr.get("icons/96px/delete.png").res)
        self.del_btn.setToolTip("Delete Items")
        self.addWidget(self.del_btn)

        self.rename_btn = QPushButton(parent=self, text="", icon=res_mgr.get("icons/96px/rename.png").res)
        self.rename_btn.setToolTip("Rename Item")
        self.addWidget(self.rename_btn)

        self.search_btn = QPushButton(parent=self, text="Search")
        self.search_btn.setToolTip("Search")
        self.addWidget(self.search_btn)


class ProjectExplorer(QWidget):
    """
        signals:
        item_operation_requested: takes List[Action] emitted when the widget requests file moves, removes, etc.
    
    """
    
    item_operation_requested = pyqtSignal(list)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.__search_term: str = ""

        self.__workdir: Optional[pathlib.Path] = None

        self.setObjectName("ProjectExplorer")
        self.__root_layout = QVBoxLayout()
        self.setLayout(self.__root_layout)
        self.__toolbar = self.__edit_toolbar()
        self.__root_layout.addWidget(self.__toolbar)

        self.__search_toolbar = SearchToolbar(self)
        self.__search_toolbar.setVisible(False)
        self.__search_toolbar.search_input.textChanged.connect(self.__on_search_update)

        self.__root_layout.addWidget(self.__search_toolbar)
        self.__project_tree = ProjectTree(self, ProjectTreeArgs(
            dir_only=False
        ))
        self.__root_layout.addWidget(self.__project_tree)
        self.__project_tree.item_clicked.connect(self.__validate_btns)
        self.__project_tree.drag_drop_item.connect(self.__on_drag_drop_item)
        self.file_clicked = self.__project_tree.item_clicked
        self.file_double_clicked = self.__project_tree.file_double_clicked
        self.__validate_btns()

    def __validate_btns(self):
        indexes_len = len(self.__project_tree.get_selected_indexes())
        has_selection = indexes_len > 0
        self.__toolbar.move_btn.setDisabled(not has_selection)
        self.__toolbar.del_btn.setDisabled(not has_selection)
        self.__toolbar.rename_btn.setDisabled(not indexes_len == 1)

    def __new_menu(self):
        new_menu = QMenu()
        new_menu.addAction("File", lambda: self.__on_new_btn(ItemRecognizedType.PWE))
        new_menu.addAction("Folder", lambda: self.__on_new_btn(ItemRecognizedType.FOLDER))
        new_menu.setStyleSheet(MainStylesheetManager().get_rule("*"))
        return new_menu

    def __get_workdir(self):
        if self.__workdir is None:
            raise GUIException("on_new_item() called without working directory")

        return self.__workdir

    def __move_item(self, move_info: MoveInfo):
        
        actions = [MoveAction(item, move_info.dest) for item in move_info.src_items]
        self.item_operation_requested.emit(actions)

        logging.debug("Updating __move_item")
        for path2 in move_info.paths_deleted:
            self.__project_tree.delete_item(path2)

        for path in move_info.items_created:
            self.__project_tree.add_item(path)

    def __on_drag_drop_item(self, info: DragDropInfo):
        self.__move_item(MoveInfo.gen_move_info(
            [self.__get_workdir() / info.src],
            self.__get_workdir() / info.dst
        ).relative_to(self.__get_workdir()))
        self.__validate_btns()
    
    def __on_move_btn(self):

        selected_items: List[pathlib.Path] = []
        for index in self.__project_tree.get_selected_indexes():
            selected_item: ItemInfo = index.data(ITEM_DATA_ROLE)
            if not isinstance(selected_item, ItemInfo):
                logging.error("Selected item is None or not pathlib.Path type=%s", type(selected_item))
                continue
            selected_items.append(selected_item.path)
        
        dialog = ItemMoveDialog(self, selected_items, self.__get_workdir())
        dialog.items_moved.connect(self.__move_item)
        dialog.exec()

    def __rename_item(self, info: RenameInfo):
        self.item_operation_requested.emit([MoveAction(info.item.path, info.full_new_path())])
        self.__project_tree.delete_item(info.item.path)
        self.__project_tree.add_item(ItemInfo(path=info.full_new_path(), item_type=info.item.item_type))
        self.__validate_btns()
        
        
    def __on_rename_btn(self):
        """
            If multiple files are selected, it only chooses the first one on the index.
            This is best used for when there are one selected items.
        """
        if len((index := self.__project_tree.get_selected_indexes())) < 1:
            return
        selected_item: ItemInfo = index[0].data(ITEM_DATA_ROLE)
        assert isinstance(selected_item, pathlib.Path)
        dialog = ItemRenameDialog(self, selected_item, self.__get_workdir())
        dialog.on_name_selected.connect(self.__rename_item)
        dialog.exec()

    def __edit_toolbar(self):
        toolbar = ProjectExplorerToolbar(self)

        toolbar.new_btn.setMenu(self.__new_menu())
        toolbar.del_btn.clicked.connect(self.__on_delete_btn)
        toolbar.move_btn.clicked.connect(self.__on_move_btn)
        toolbar.rename_btn.clicked.connect(self.__on_rename_btn)
        toolbar.search_btn.clicked.connect(self.__toggle_search)
        return toolbar

    def __create_new_item(self, item: ItemCreationResult):
        self.item_operation_requested.emit([NewItemAction(item.path, item.recognized_type == ItemRecognizedType.FOLDER)])
        item_type = ItemType.FOLDER if item.recognized_type == ItemRecognizedType.FOLDER else ItemType.FILE
        self.__project_tree.add_item(ItemInfo(item.path, item_type))
        self.__validate_btns()
        # self.__index_dict[item.path.parent.as_posix()].appendRow(project_item)
        # self.__index_dict[item.path.as_posix()] = project_item

    def __delete_item(self, item: pathlib.Path):
        self.item_operation_requested.emit([DeleteAction(item)])
        self.__validate_btns()

    def __on_delete_btn(self):
        for index in self.__project_tree.get_selected_indexes():
            selected_item: ItemInfo = index.data(ITEM_DATA_ROLE)
            if not isinstance(selected_item, pathlib.Path):
                logging.error("Selected item is None or not pathlib.Path type=%s", type(selected_item))
                continue
            self.__delete_item(selected_item)
            self.__project_tree.delete_item(selected_item)
            
    def __on_new_btn(self, item_type: ItemRecognizedType):
        workdir = self.__get_workdir()
        selected_path = self.__project_tree.get_cur_selected_path()
        
        if not selected_path:
            dir_to_create = workdir.relative_to(workdir)
        else:
            abs_path = workdir / selected_path
            if abs_path.is_dir():
                dir_to_create = selected_path
            else:
                dir_to_create = selected_path.parent

        
        dialog = ItemNewDialog(self, item_type, dir_to_create, workdir)
        dialog.on_name_selected.connect(self.__create_new_item)
        dialog.exec()


    def __get_folder(self):
        if self.__workdir is None:
            raise ValueError("__get_folder called while self.__workdir is None")
        return walk_and_return_folder_item(self.__workdir).sorted(key=sort_alphabetically_key)

    def load(self, directory: pathlib.Path):
        """
            Loads the widget with a specific path
        """
        self.__workdir = directory
        self.__project_tree.load_folder(self.__get_folder())

    def test_move_item(self, move_info: MoveInfo):
        """
            Testing purposes only.
        """
        self.__move_item(move_info)

    def __toggle_search(self):
        is_visible = self.__search_toolbar.isVisible()
        if is_visible:
            self.__search_term = ""
        else:
            self.__on_search_update()

        self.__search_toolbar.setVisible(not is_visible)
        
    def __on_search_update(self):
        self.__search_term = self.__search_toolbar.search_input.text().strip()

        self.__project_tree.load_folder(self.__get_folder().file_filter(lambda f: f.name().find(self.__search_term) != -1))
        #logging.debug("Search term: %s", self.__search_term)