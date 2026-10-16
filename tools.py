from pathlib import Path

import click

from tools.migrate import migrate_file_to_sql_wiki

@click.group()
def cli():
    pass

@click.command()
@click.argument("destination")
def convert_endtest_wikis(destination: str):
    wikis_path = Path("./end-tests/wikis")
    for wiki in wikis_path.iterdir():        
        migrate_file_to_sql_wiki(wiki, Path(destination))

cli.add_command(convert_endtest_wikis)

if __name__ == '__main__':
    cli()