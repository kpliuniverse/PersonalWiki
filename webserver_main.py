import os
import pathlib

from werkzeug import Request, Response
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple


class WebServer(object):
    def view(self, md):
        return Response(str(md))   

    def wsgi_app(self, environ, start_response):
        self.url_map = Map([
            Rule('/view/<md>', endpoint='view'),
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


if __name__ == "__main__": 
    run_simple("127.0.0.1", 8080, WebServer())