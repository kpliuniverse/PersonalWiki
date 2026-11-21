import pathlib
from typing import NoReturn

import click

from src.app import App, AppArgs
import logging

from src.utils.wiki_utils import walk_and_return_folder_item

@click.command()
@click.argument("pwe_file", type=click.Path(dir_okay=False, readable=True, writable=True, exists=True), default=None)
def main(pwe_file) -> NoReturn:
    import multiprocessing
    multiprocessing.freeze_support()
    
    app_args = AppArgs(
        pwe_file
    )
    App(app_args).run()

if __name__ == "__main__":
    main()
