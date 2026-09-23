import base64
import logging
import os
import pathlib
import sys
from typing import override

import waitress
from werkzeug import Request, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple
from werkzeug.middleware.shared_data import SharedDataMiddleware
from src.consts import LOOPBACK_IP_ADD, PROJECT_ROOT, WIKI_ENCODING
from src.multiprocessing.child_process import ChildProcess
from src.parser.markdown_parser import parse_md_to_html
from src.states.appstate import AppState
from src.templating.templating import MainHTMLTemplater

import importlib

from src import consts
from src.utils.encoding import url_b64_decode
from src.wiki.wiki import WikiFileMode



class WebServer(object):
    """
        The WebServer object

        args:
        root_path: pathlib.Path that links to the root path. Highly reccommend that this is absolute
    """
    def __init__(self, app_state: AppState):
        self.app_state = app_state
        
    def view(self, args):
        rel_path = pathlib.Path(url_b64_decode(args["path"]).decode(WIKI_ENCODING).replace("\\", "/"))

        with self.app_state.cur_wiki.open_wikifile(rel_path, WikiFileMode.READ) as f:
            md_content: str = f.read()
        context = {
            "body": parse_md_to_html(md_content)
        }
        
        return Response(MainHTMLTemplater().render(context), mimetype="text/html")

    def wsgi_app(self, environ, start_response):
        self.url_map = Map([
            Rule('/view/<path>', endpoint='view'),
            Rule('/exit', endpoint='exit')
        ])
        request = Request(environ)

        adapter = self.url_map.bind_to_environ(request.environ)

        try:

            endpoint, values = adapter.match()
            
            if endpoint == "view":
                response = self.view(values)
                return response(environ, start_response)

            else:
                raise NotFound()
            
        except HTTPException as e:
            return Response(str(e))(environ, start_response)
    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)
# create_environ(".testenv/wikis/basic", "http://localhost:8080")




WEBSERVER_PORT = 8080

def create_app(app_state: AppState):
    app = WebServer(app_state=app_state)
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/default_static':  (PROJECT_ROOT / "src/static").as_posix()
    })
    return app

class WebserverProcess(ChildProcess):
    def __init__(self, app_state: AppState):
        self.port = WEBSERVER_PORT
        self.host = LOOPBACK_IP_ADD
        self.app_state = app_state

    @override
    def run(self):
        waitress.serve(create_app(self.app_state), host=self.host, port=self.port)

    