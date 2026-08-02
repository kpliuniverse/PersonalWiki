import pathlib


def gen_path_string(working_directory: pathlib.Path, wiki_directory: pathlib.Path):
    """
        Generate path string. Working directory must be related to wiki directory e.g. referencing item in /c/d in wiki a must be passed as a/c/d
    """

    if not working_directory.relative_to(wiki_directory):
        raise ValueError(f"Working directory ({working_directory} is not related to wiki directory ({wiki_directory})")
    if (working_directory == wiki_directory):
        return "/"
    else:
        return f"/{(working_directory.relative_to(wiki_directory)).as_posix()}"