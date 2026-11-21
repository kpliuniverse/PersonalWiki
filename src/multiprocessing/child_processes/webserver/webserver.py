
import multiprocessing.synchronize as sync
import pathlib
from typing import override

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from src.consts import LOOPBACK_IP_ADD, PROJECT_ROOT
from src.multiprocessing.child_process import ChildProcess
from src.parser.markdown_parser import parse_md_to_html
from src.states.appstate import AppState, PickleableAppState
from src.templating.templating import MainHTMLTemplater
from src.wiki.wiki import DEFAULT_READ_MODE, Wiki

WEBSERVER_PORT = 8080
class WebServerFactory:

    def __call__(self):
        app = FastAPI()

        @app.get("/view/{path:path}", response_class=HTMLResponse)
        def view(path) -> str:
            rel_path = pathlib.Path(path)

            with self.lock, self.app_state.cur_wiki.open_wikifile(rel_path, DEFAULT_READ_MODE) as f:
                    md_content: str = f.read() # type: ignore
                
            context: dict[str, str] = {
                "body": parse_md_to_html(md_content)
            }
            content = MainHTMLTemplater().render(context)
            return content

        app.mount("/default_static/", StaticFiles(directory=(PROJECT_ROOT / "src/static").as_posix()), name="default_static")
        return app
         
    def __init__(self, app_state: PickleableAppState, lock: sync.Lock) -> None:
        
        self.app_state = AppState()
        self.app_state.cur_wiki = Wiki(
            path_dir=app_state.wiki_state.path_dir, 
            session=app_state.wiki_state.cur_session, 
            settings=app_state.wiki_state.cur_settings
        )
        self.lock: sync.Lock = lock


        

        
# def web_app(app_state: PickleableAppState, lock: sync.Lock):
#     app = FastAPI()

#     @app.get("/view/{path:path}")
#     async def read_file(path: str):

#         with self.lock, self.app_state.cur_wiki.open_wikifile(rel_path, DEFAULT_READ_MODE) as f:
#                 md_content: str = f.read() # type: ignore
            
#         context: dict[str, str] = {
#             "body": parse_md_to_html(md_content)
#         }
    

class WebserverProcess(ChildProcess):
    def __init__(self, app_state: PickleableAppState, lock: sync.Lock) -> None:
        self.port: int = WEBSERVER_PORT
        self.host: str = LOOPBACK_IP_ADD
        self.app_state: PickleableAppState = app_state
        self.lock: sync.Lock = lock

    @override
    def run(self) -> None:
        app = WebServerFactory(app_state=self.app_state, lock=self.lock)
        uvicorn.run(app(), host=self.host, port=self.port)