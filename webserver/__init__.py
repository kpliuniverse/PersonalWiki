import os
import sys
from flask import Flask


def create_app(test_config=None):
    print(__name__)
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        
        return 'Hello, World!'

    @app.route('/quit')
    def app_quit():
        raise KeyboardInterrupt

    return app

