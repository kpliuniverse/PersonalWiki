import os
import sys

from werkzeug import run_simple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


from src.multiprocessing.child_processes.webserver import WebserverProcess


if __name__ == "__main__": 

    WebserverProcess().run()
    # run_simple("127.0.0.1", 8080, create_app(), use_reloader=True)

    # waitress.serve(create_app(), host="127.0.0.1", port=8080)