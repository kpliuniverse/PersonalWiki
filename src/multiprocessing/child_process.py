
from abc import abstractmethod
from typing import Protocol


class ChildProcess(Protocol):
    """
        Protocol for childprocesses

        Every class that implements it must have init that take shell-like arguments as list[str]

        Contains two methods, `run` and `close`. The former is an abstract method, so overriding it is mandatory.
    """

    @abstractmethod
    def __init__(self, args: list[str]): ...
    
    @abstractmethod
    def run(self): ...

    def close(self):
        pass