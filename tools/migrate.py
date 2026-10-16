import os
from pathlib import Path
import shutil
from src.utils.path_utils import path_dot
from src.wiki.wiki import Wiki, create_wiki, open_wiki

def migrate_file_to_sql_wiki(wiki_dir: Path, migrated_dir: Path):
    new_wiki = create_wiki(migrated_dir, wiki_dir.name)


    shutil.copy(wiki_dir / "wiki.pwi", new_wiki.get_wiki_dir_path())

    try:
        shutil.copytree(wiki_dir / ".pw", new_wiki.get_wiki_dir_path() / ".pw")
    except FileNotFoundError:
        pass
    wiki = open_wiki(new_wiki.get_wiki_dir_path() / "wiki.pwi")

    old_proper = wiki_dir / "proper"
    for dir_path, _, file_names in os.walk(old_proper):
        dir_path = Path(dir_path)
        rel_dir_path = dir_path.relative_to(old_proper)
        if rel_dir_path != path_dot():
            wiki.mkdir(rel_dir_path)

        for file_name in file_names:
            wiki.import_file(dir_path / file_name, rel_dir_path / file_name)  

          