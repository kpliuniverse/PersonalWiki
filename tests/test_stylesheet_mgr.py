import logging
import pathlib

from src.ui.stylesheets.app_stylesheet import StylesheetManager


def test_child_elements():
    mgr = StylesheetManager(load_path=pathlib.Path(__file__).parent / "input/test.scss")
    assert mgr.get_rule("a") == r"a{b:c;} a c{d:e;} a b{a:b;} a c b{f:e;}"
    assert mgr.get_rule("a c") == r"a c{d:e;} a c b{f:e;}"
    assert mgr.get_rule("a b") == r"a b{a:b;}"
    assert mgr.get_rule("nonexistent") is None
    assert mgr.get_rule("multiple-rule") == r"multiple-rule{a:b;} multiple-rule{c:d;}"
    assert mgr.get_rule("a.b") == r"a.b{a:b;}"

def test_universal_and_subcat():
    mgr = StylesheetManager(load_path=pathlib.Path(__file__).parent / "input/universaltest.scss")
    universal = r"*{answer:42;}"
    assert mgr.get_rule("*") == universal
    assert mgr.get_rule("elem1") == f"{universal} elem1{{a:b;}}"
    assert mgr.get_rule("elem2") == f"{universal} elem2{{a:b;}} elem2#c{{c:d;}}"