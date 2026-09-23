import time

from src.multiprocessing import multiprocessing
from src.multiprocessing.child_processes.webserver import WebserverProcess

from returns.result import Failure, Success

def test_close(tmp_path):
    mgr = multiprocessing.MultiprocessingManager()
    match mgr.run_process(WebserverProcess(tmp_path)):
        case Failure(e):
            raise multiprocessing.MultiprocessingException(e)
        case Success(i_d):
            time.sleep(1)
            mgr.close_process(i_d)