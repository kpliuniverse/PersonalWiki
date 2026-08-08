from abc import ABC
import pathlib

from attr import define, frozen

class Action(ABC):
    pass

@frozen
class MoveAction(Action):
    src: pathlib.Path
    dst: pathlib.Path

@frozen
class CopyAction(Action):
    src: pathlib.Path
    dst: pathlib.Path

@frozen
class DeleteAction(Action):
    target: pathlib.Path

@frozen
class NewItemAction(Action):
    target: pathlib.Path
    is_dir: bool
