import logging
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def pytest_configure(config):
    import multiprocessing
    multiprocessing.freeze_support()

from src.wiki.wiki import create_wiki
from tests.utils.path_utils import gen_available_name


@pytest.fixture
def wiki(tmp_path_factory):
    base_temp = tmp_path_factory.mktemp("wiki")
    return create_wiki(base_temp, gen_available_name(base_temp))