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
from src.templating.templating import MainHTMLTemplater

import importlib

from src import consts
from src.utils.encoding import url_b64_decode



class WebServer(object):
    """
        The WebServer object

        args:
        root_path: pathlib.Path that links to the root path. Highly reccommend that this is absolute
    """
    def __init__(self, root_path: pathlib.Path):
        self.root_path = root_path
        
    def view(self, args):
        rel_path = pathlib.Path(url_b64_decode(args["path"]).decode(WIKI_ENCODING).replace("\\", "/"))
        path = self.root_path / rel_path
        with open(path, encoding=WIKI_ENCODING) as f:
            md = f.read()

        context = {
            "body": parse_md_to_html(md)
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


def create_app(path: pathlib.Path):
    app = WebServer(root_path=path)
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/default_static':  (PROJECT_ROOT / "src/static").as_posix()
    })
    return app

WEBSERVER_PORT = 8080

class WebserverProcess(ChildProcess):
    def __init__(self, path: pathlib.Path):
        self.port = WEBSERVER_PORT
        self.host = LOOPBACK_IP_ADD
        self.path = path

    @override
    def run(self):
        waitress.serve(create_app(self.path), host=self.host, port=self.port)

    