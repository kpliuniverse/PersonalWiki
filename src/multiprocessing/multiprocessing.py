

from enum import IntEnum, StrEnum, auto
from multiprocessing import Process
from typing import Callable, Dict, Self
from uuid import UUID, uuid7

import attrs

from returns.result import Failure, Result, ResultE, Success, safe

from src.multiprocessing.child_process import ChildProcess
from src.utils.singleton import Singleton

class MultiprocessingException(BaseException):
    pass
class ProcessStatus(IntEnum):
    """
        Consists of three values.

        READY - process is added to the processes dict but not running
        RUNNING - process is running
        TERMINATED - process has exited
    """
    READY = auto()
    RUNNING = auto()
    TERMINATED = auto()

@attrs.define
class ChildProcessInfo:
    close_function: Callable[[], None]
    process: Process
    status: ProcessStatus

class MultiprocessingError(StrEnum):
    ProcessNotFound = auto()
    ProcessFailedToStart = auto()

class MultiprocessingManager(metaclass=Singleton):
    # In this code, it is written i_d because it conflicts with id builtin function, though the latter is unused.
    def __init__(self):
        self.__processes: Dict[UUID, ChildProcessInfo] = {}

    def ready_process(self, process: ChildProcess) -> UUID:
        """
            Add process to the process dict. (This is called readying)

            Returns its UUID
        """
        while True:
            i_d = uuid7()
            if i_d not in self.__processes:
                break
        
        self.__processes[i_d] = ChildProcessInfo(
            close_function=process.close,
            process=Process(target=ChildProcess.run),
            status=ProcessStatus.READY
        )
        return i_d

    def run_readied_process(self, i_d: UUID) -> Result[None, MultiprocessingError]:
        """
            Run readied process.

            You should get the uuid from ready_process
        """
        if (child_process_info := self.__processes.get(i_d, None)) is None:
            return Failure(MultiprocessingError.ProcessNotFound)
        child_process_info.process.start()
        child_process_info.process.join()
        return Success(None)

    def run_process(self, process: ChildProcess) -> Result[UUID, MultiprocessingError]:
        """
            Immediately run a process.
        """
        i_d = self.ready_process(process)
        return self.run_readied_process(i_d).map(lambda _: i_d)

    def get_status(self, i_d: UUID) -> ProcessStatus:
        return self.__processes[i_d].status

    @safe
    def close_process(self, i_d: UUID):
        """
            returns ResultE
        """
        self.__processes[i_d].close_function()
        self.__processes[i_d].process.terminate()

    @safe
    def close_all(self):
        for i_d in self.__processes.keys():
            self.close_process(i_d)
    
        
        
