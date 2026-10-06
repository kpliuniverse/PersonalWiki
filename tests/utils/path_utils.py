import logging
import pathlib
import tempfile


def gen_available_name(directory: pathlib.Path):
    with tempfile.NamedTemporaryFile(dir=directory, delete_on_close=True) as t:
        gen_file_path = pathlib.Path(t.name)
        logging.info("Generated throwaway %s", gen_file_path.as_posix())
    if gen_file_path.exists():
        raise FileExistsError("Throwaway file not deleted")
    return gen_file_path.name

