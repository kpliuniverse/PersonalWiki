import pathlib


def gen_path_string(item_path: pathlib.Path, wiki_directory: pathlib.Path):
    """
        Generate path string. Working directory must be related to wiki directory e.g. referencing item in /c/d in wiki a must be passed as a/c/d
    """

    if not item_path.relative_to(wiki_directory):
        raise ValueError(f"Item path ({item_path} is not related to wiki directory ({wiki_directory})")
    if (item_path == wiki_directory):
        return "/"
    else:
        return f"/{(item_path.relative_to(wiki_directory)).as_posix()}"


