import pathlib
from typing import NoReturn

from src.app import App
import logging

from src.utils.wiki_utils import walk_and_return_folder_item


def main() -> NoReturn:
    import multiprocessing
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.DEBUG)
    App().run()

if __name__ == "__main__":
    main()
