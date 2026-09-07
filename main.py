import pathlib

from src.app import App
import logging

from src.utils.wiki_utils import walk_and_return_folder_item


def main():
    logging.basicConfig(level=logging.DEBUG)
    walk_and_return_folder_item(pathlib.Path("end-tests/folders/walktest"))
    #App().run()

if __name__ == "__main__":
    main()
