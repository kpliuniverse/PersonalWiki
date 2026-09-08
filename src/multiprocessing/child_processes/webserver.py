import base64
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
from src.parser.markdown_parser import parse_chunk
from src.templating.templating import MainHTMLTemplater

import importlib

from src import consts



class WebServer(object):
    def view(self, args):
        path: str = base64.b64decode(args["path"], altchars=b'-_').decode(WIKI_ENCODING)
        with open(f"/{path.replace("\\", "/")}", encoding=WIKI_ENCODING) as f:
            md = f.read()

        context = {
            "body": parse_chunk(md)
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


def create_app():
    app = WebServer()
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/default_static':  (PROJECT_ROOT / "src/static").as_posix()
    })
    return app


class WebserverProcess(ChildProcess):
    def __init__(self):
        self.port = 8080
        self.host = LOOPBACK_IP_ADD

    @override
    def run(self):
        waitress.serve(create_app(), host=self.host, port=self.port)

    