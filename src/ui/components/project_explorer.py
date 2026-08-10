import logging
import pathlib
from PyQt6.QtCore import Qt, pyqtSignal 
from PyQt6.QtWidgets import (
    QMenu,
    QWidget, 
    QVBoxLayout, 
    QToolBar, 
    QPushButton
)

from src.ui.components.dialogs.item_move_dialog import ItemMoveDialog
from src.ui.components.dialogs.item_rename_dialog import ItemRenameDialog, RenameInfo
from src.utils.item_actions import DeleteAction, MoveAction, NewItemAction
from src.utils.move_info import MoveInfo
from src.ui.components.dialogs.item_name_dialog import ItemNameDialog
from src.ui.components.project_tree import DragDropInfo, ProjectTree, ProjectTreeArgs
from src.exceptions import GUIException
from src.items.items import ItemCreationResult, ItemType


class ToolBar(QToolBar):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.new_btn = QPushButton(parent=self, text="New")
        self.addWidget(self.new_btn)

        self.move_btn = QPushButton(parent=self, text="Move")
        self.addWidget(self.move_btn)

        self.del_btn = QPushButton(parent=self, text="Delete")
        self.addWidget(self.del_btn)

        self.rename_btn = QPushButton(parent=self, text="Rename")
        self.addWidget(self.rename_btn)

class ProjectExplorer(QWidget):
    """
        signals:
        item_operation_requested: takes List[Action] emitted when the widget requests file moves, removes, etc.
    
    """
    
    item_operation_requested = pyqtSignal(list)
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.__root_layout = QVBoxLayout()
        self.setLayout(self.__root_layout)
        self.__toolbar = self.__edit_toolbar()
        self.__root_layout.addWidget(self.__toolbar)
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
        new_menu.addAction("File", lambda: self.__on_new_btn(ItemType["PWE"]))
        new_menu.addAction("Folder", lambda: self.__on_new_btn(ItemType["FOLDER"]))
        return new_menu

    def __get_workdir(self):
        workdir = self.__project_tree.get_working_directory()

        if workdir is None:
            raise GUIException("on_new_item() called without working directory")

        return workdir

    def __move_item(self, move_info: MoveInfo):
        
        actions = [MoveAction(item, move_info.dest) for item in move_info.src_items]
        self.item_operation_requested.emit(actions)

        logging.debug("Updating __move_item")
        for path2 in move_info.paths_deleted:
            self.__project_tree.delete_item(path2)

        for path in move_info.paths_created:
            self.__project_tree.add_item(path)

    def __on_drag_drop_item(self, info: DragDropInfo):
        self.__move_item(MoveInfo.gen_move_info(
            [self.__get_workdir() / info.src],
            self.__get_workdir() / info.dst
        ).relative_to(self.__get_workdir()))
        self.__validate_btns()
    
    def __on_move_btn(self):

        selected_items = []
        for index in self.__project_tree.get_selected_indexes():
            selected_item: pathlib.Path = index.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(selected_item, pathlib.Path):
                logging.error("Selected item is None or not pathlib.Path type=%s", type(selected_item))
                continue
            selected_items.append(selected_item)
        
        dialog = ItemMoveDialog(self, selected_items, self.__get_workdir())
        dialog.items_moved.connect(self.__move_item)
        dialog.exec()

    def __rename_item(self, info: RenameInfo):
        self.item_operation_requested.emit([MoveAction(info.file, info.full_new_name())])
        self.__project_tree.delete_item(info.file)
        self.__project_tree.add_item(info.full_new_name())
        self.__validate_btns()
        
        
    def __on_rename_btn(self):
        if len((index := self.__project_tree.get_selected_indexes())) > 1:
            # TODO: MessageBox that displays 'You can't rename files'
            return
        selected_item: pathlib.Path = index[0].data(Qt.ItemDataRole.UserRole + 1)
        assert isinstance(selected_item, pathlib.Path)
        dialog = ItemRenameDialog(self, selected_item, self.__get_workdir())
        dialog.on_name_selected.connect(self.__rename_item)
        dialog.exec()

    def __edit_toolbar(self):
        toolbar = ToolBar(self)

        toolbar.new_btn.setMenu(self.__new_menu())
        toolbar.del_btn.clicked.connect(self.__on_delete_btn)
        toolbar.move_btn.clicked.connect(self.__on_move_btn)
        toolbar.rename_btn.clicked.connect(self.__on_rename_btn)
        return toolbar

    def __create_new_item(self, item: ItemCreationResult):
        self.item_operation_requested.emit([NewItemAction(item.path, item.typ == ItemType["FOLDER"])])
        self.__project_tree.add_item(item.path)
        self.__validate_btns()
        # self.__index_dict[item.path.parent.as_posix()].appendRow(project_item)
        # self.__index_dict[item.path.as_posix()] = project_item

    def __delete_item(self, item: pathlib.Path):
        self.item_operation_requested.emit([DeleteAction(item)])
        self.__validate_btns()

    def __on_delete_btn(self):
        for index in self.__project_tree.get_selected_indexes():
            selected_item: pathlib.Path = index.data(Qt.ItemDataRole.UserRole + 1)
            if not isinstance(selected_item, pathlib.Path):
                logging.error("Selected item is None or not pathlib.Path type=%s", type(selected_item))
                continue
            self.__delete_item(selected_item)
            self.__project_tree.delete_item(selected_item)
            
    def __on_new_btn(self, item_type: ItemType):
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

        
        dialog = ItemNameDialog(self, item_type, dir_to_create, workdir)
        dialog.on_name_selected.connect(self.__create_new_item)
        dialog.exec()

    def load(self, directory: pathlib.Path):
        """
            Loads the widget with a specific path
        """
        self.__project_tree.load(directory)

    def test_move_item(self, move_info: MoveInfo):
        """
            Testing purposes only.
        """
        self.__move_item(move_info)