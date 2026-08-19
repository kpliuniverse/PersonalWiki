
import json
import logging
import pathlib
import shutil
import tempfile

import pytest

from src.wiki.wiki import create_wiki, open_wiki


def test_open_path(): 

    wiki_dir = pathlib.Path("end-tests/wikis/basic")
    wiki = open_wiki(wiki_dir / "wiki.pwi")
    with open(wiki_dir / ".pw" / "session.json", "r", encoding="utf-8") as session:
        session_json = json.load(session)
    assert wiki.get_cur_item() == session_json["currentFile"] 
    assert wiki.get_cur_item_abs() == wiki_dir / "proper" / session_json["currentFile"]

    with pytest.raises(FileNotFoundError):
        open_wiki(pathlib.Path("end-tests/wikis/does-not-exist/wiki.pwi"))

def test_create_wiki(tmp_path: pathlib.Path):
    temp_end_tests = tmp_path / "end-tests"
    shutil.copytree("end-tests", temp_end_tests)

    temp_wikis = temp_end_tests / "wikis"

    # To generate a folder name
    with tempfile.NamedTemporaryFile(dir=temp_wikis, delete_on_close=True) as t:
        gen_file_path = pathlib.Path(t.name)
        logging.info("Generated throwaway %s", gen_file_path.as_posix())
    if gen_file_path.exists():
        raise FileExistsError("Throwaway file not deleted")

    wiki = create_wiki(gen_file_path.parent, gen_file_path.name)
    assert gen_file_path.is_dir()
    assert (gen_file_path / "proper").is_dir()
    assert (gen_file_path / "wiki.pwi").is_file()

