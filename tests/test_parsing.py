import html
import logging

from src.parser.markdown_parser import parse_md_to_html

def test_escape_tags_and_html_escaping():
    """
        Test whenever this escapes special HTML characters to prevent XSS and also test special tags
    """

    def parse(md):
        return parse_md_to_html(md).strip()

    def enclose(h):
        return f"<p>{h}</p>"
    
    TESTS = [
        "<le>b<ge><le>/b<ge>",
        "\"You're a freak. A daughter of a tyrant\", they said.",
        "<le>script<ge>alert(\"Hax0rd\")<le>/script<ge>",
    ]

    assert parse("<lt>b<gt>a<lt>/b<gt>") == enclose(html.escape("<b>a</b>"))
    assert parse("Line<br>break") == enclose("Line<br>break")
    # for md in TESTS:
    #     html_out = parse_md(md)
    #     assert isinstance(html_out, str)
    #     assert html_out.strip() == f"<p>{html.escape(md)}</p>"

def test_false_harmful_link():
    assert parse_md_to_html("[hello](wiki://hello)").strip("\n") == '<p><a href="wiki://hello">hello</a></p>'

