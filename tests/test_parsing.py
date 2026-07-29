import html

from src.parser.markdownparser import parse_markdown

def test_escape():
    strings = [
        "<b></b>",
        "<script>alert(\"You've been hacked!\")</script>",
        "R&B"
    ]
    for string in strings:
        assert parse_markdown(string) == html.escape(string)