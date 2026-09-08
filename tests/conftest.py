import logging
import os
import sys

def pytest_configure(config):
    import multiprocessing
    multiprocessing.freeze_support()
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
