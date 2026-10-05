
import re




def is_valid_item_name(filename: str):
    filename_stripped = filename.strip()
    return all([
        filename_stripped not in ["", ".", "..", "(root)"],
        re.search("[\\\\/&?!<>:\"|?* ]", filename_stripped) is None,
    ])
        