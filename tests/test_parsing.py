import html

from src.parser.markdown_parser import parse_chunk

def test_escape():

    TESTS = [
        "<b></b>",
        "\"You're a freak. A daughter of a tyrant\", they said.",
        "<script>alert(\"Hax0rd\")</script>",
    ]

    for md in TESTS:
        chunk = parse_chunk(md)
        assert isinstance(chunk, str)
        assert chunk.strip() == f"<p>{html.escape(md)}</p>"