from abc import abstractmethod
import pathlib
from typing import Protocol, runtime_checkable

from PyQt6.QtCore import pyqtSignal

@runtime_checkable
class Loadable(Protocol):
    """
        Implement if the widget depends on a path upon load

        Implement by having a method as follows: def load_item(self, item: pathlib.Path)
    """
    @abstractmethod
    def load_item(self, item: pathlib.Path): ...


@runtime_checkable
class Savable(Protocol):
    """
        Implement if the widget should respond to save commands.

        Implement by having a method as follows: def save_cur_item(self)
    """
    @abstractmethod
    def save_cur_item(self): ...


@runtime_checkable
class CanSwitchToOtherItems(Protocol):
    """
        Implement if the widget have the ability to switch to other items.
        
        Implement by having a protocol member called switch_signal that must be pyqtSignal(pathlib.Path)
    """
    switch_signal: pyqtSignal