

from enum import IntEnum, StrEnum, auto
import logging
from multiprocessing import Lock, Process
from typing import Callable, Dict, Self
from uuid import UUID, uuid7

import attrs

import dill
from returns.result import Failure, Result, ResultE, Success, safe

from src.multiprocessing.child_process import ChildProcess
from src.utils.singleton import Singleton


class GlobalLock(metaclass=Singleton):
    def __init__(self):
        self.__lock = Lock()

    def lock(self):
        return self.__lock
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
            process=Process(target=process.run, ),
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
#child_process_info.process.join()
        if child_process_info.process.exitcode is not None:
            return Failure(MultiprocessingError.ProcessFailedToStart)
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
        logging.info("closing %s", i_d)
        self.__processes[i_d].close_function()
        self.__processes[i_d].process.terminate()
        self.__processes[i_d].status = ProcessStatus.TERMINATED
        logging.info("closed %s", i_d)

    @safe
    def close_all(self):
        for i_d in self.__processes.keys():
            self.close_process(i_d)
            
    @safe
    def kill_all(self):
        logging.info("Force closing processes")
        for i_d, process in self.__processes.items():
            if process.status != ProcessStatus.TERMINATED and process.process.is_alive():
                process.process.kill()
                self.__processes[i_d].status = ProcessStatus.TERMINATED
                logging.info("Killed %s", i_d)
        
