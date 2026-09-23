import pathlib
import time

from src.multiprocessing import multiprocessing
from src.multiprocessing.child_processes.webserver import WebserverProcess

from returns.result import Failure, Success

from src.states.appstate import AppState
from src.wiki.wiki import open_wiki

def test_close():
    mgr = multiprocessing.MultiprocessingManager()
    app_state = AppState()
    app_state.cur_wiki = open_wiki(pathlib.Path(__file__).parent.parent / ".testenv/wikis/blank")
    match mgr.run_process(WebserverProcess(app_state)):
        case Failure(e):
            raise multiprocessing.MultiprocessingException(e)
        case Success(i_d):
            time.sleep(1)
            mgr.close_process(i_d)