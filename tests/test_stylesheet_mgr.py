import logging
import pathlib

from src.ui.stylesheets.stylesheet import StylesheetManager


def test_child_elements():
    mgr = StylesheetManager(load_path=pathlib.Path(__file__).parent / "input/test.scss")
    assert mgr.get_rule("a") == r"a{b:c;} a c{d:e;} a b{a:b;} a c b{f:e;}"
    assert mgr.get_rule("a c") == r"a c{d:e;} a c b{f:e;}"
    assert mgr.get_rule("a b") == r"a b{a:b;}"
    assert mgr.get_rule("nonexistent") is None
    assert mgr.get_rule("multiple-rule") == r"multiple-rule{a:b;} multiple-rule{c:d;}"
    assert mgr.get_rule("a.b") == r"a.b{a:b;}"

def test_universal():
    mgr = StylesheetManager(load_path=pathlib.Path(__file__).parent / "input/universaltest.scss")
    assert mgr.get_rule("*") == r"*{answer:42;}"
    assert mgr.get_rule("elem1") == r"*{answer:42;} elem1{a:b;}"