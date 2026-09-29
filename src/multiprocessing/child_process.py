
from abc import abstractmethod
from typing import Protocol


class ChildProcess(Protocol):
    """
        Protocol for childprocesses

        Contains two methods, `run` and `close`. The former is an abstract method, so overriding it is mandatory.
    """

    @abstractmethod
    def run(self): ...

    def close(self):
        pass