from collections import deque
from copy import deepcopy
from io import TextIOWrapper
import pkgutil
import pathlib
from typing import Dict, List, Optional

import sass
import tinycss2

from tinycss2 import ast

from src.utils.package_utils import get_data_and_raise_if_none
from src.utils.singleton import Singleton


class StylesheetRule:
    def __init__(self) -> None:
        self.rule: list[ast.QualifiedRule] = []
        self.rules_for_children: Dict[str, StylesheetRule] = {}


def remove_whitespace(node_list: List[ast.Node]) -> List[ast.Node]:
    """
        Remove WhitespaceToken in node_list
    """
    return [p for p in node_list if not isinstance(p, ast.WhitespaceToken)]

def convert_rules_to_string(qualified_rules: List[ast.QualifiedRule]) -> str:
    """
        Convert list of rules to final string    
    """
    return " ".join([rule.serialize().replace("/**/", " ") for rule in qualified_rules])

class StylesheetManager():
    """
        constructor arguments:
            `data`, optional, raw_string of Sass css
            `load_path`, if `data` is not supplied, the path to load
    """
    def __init__(self, load_path: Optional[pathlib.Path] = None, data: Optional[str] = None) -> None:
        self.__root_rule: StylesheetRule = StylesheetRule()
        
        if data is None:
            if load_path is None:
                raise ValueError("Both arguments are None.")
            with open(load_path, encoding="utf-8") as scss:
                data = scss.read()

        qss: str = sass.compile(string=data) # type: ignore
        stylesheet: List[ast.QualifiedRule | ast.AtRule | ast.Comment | ast.WhitespaceToken | ast.ParseError] = tinycss2.parse_stylesheet(qss, skip_comments=True, skip_whitespace=True)
        for rule in stylesheet:
            if isinstance(rule, ast.QualifiedRule):
                key: str = tinycss2.serialize(rule.prelude).strip()
                rule_copy: ast.QualifiedRule = deepcopy(rule)
                rule_copy.prelude = remove_whitespace(rule_copy.prelude)
                rule_copy.content = remove_whitespace(rule_copy.content)
                cur_rule: StylesheetRule = self.__root_rule
                final_elems = []
                for elem in key.split(" "):
                    first_separator_index: List[int] = [
                        ind for ind in
                        (elem.find(sep) for sep in ["#", "::", ":"])
                        if ind != -1
                    ]
                    first_separator_index: int | None = min(first_separator_index) if first_separator_index else None
                    
                    if first_separator_index is not None:
                        elem: str = elem[:first_separator_index]
                        
                    if elem not in cur_rule.rules_for_children:
                        cur_rule.rules_for_children[elem] = StylesheetRule()
                    cur_rule: StylesheetRule = cur_rule.rules_for_children[elem]
                    final_elems.append(elem)
                cur_rule.rule.append(rule_copy)

    def get_rule(self, selector: str, return_universals_even_if_not_found = False) -> Optional[str]:
        """
            Get rule from selectors

            Returns None when there isn't available

            Is sorted by increasing specificity, e.g. 'a b c' is placed later than 'a b'
        """
        cur_rule: StylesheetRule = self.__root_rule
        qualified_rules: list[ast.QualifiedRule] = []
        last_elem = None
        for elem in selector.split(" "):
            if (child := cur_rule.rules_for_children.get("*", None)) is not None:
                qualified_rules.extend(child.rule)

            cur_rule: StylesheetRule | None = cur_rule.rules_for_children.get(elem, None)
            if cur_rule is None:
                if return_universals_even_if_not_found:
                    return convert_rules_to_string(qualified_rules)
                return None
            
            last_elem: str = elem
        if last_elem is not None and last_elem == "*":
            return convert_rules_to_string(qualified_rules)
        rule_queue: deque[StylesheetRule] = deque([cur_rule])
        while rule_queue:
            cur_qrule: StylesheetRule = rule_queue.popleft()
            if cur_qrule.rule is not None:
                qualified_rules.extend(cur_qrule.rule)
                
            for v in cur_qrule.rules_for_children.values():
                rule_queue.append(v)

        return convert_rules_to_string(qualified_rules)


class MainStylesheetManager(StylesheetManager, metaclass=Singleton):
    """
        A version of StylesheetManager that is a singleton automatically loads app_stylesheet.scss
    """
    def __init__(self) -> None:
        super().__init__(data=get_data_and_raise_if_none("src.ui.stylesheets", "app_stylesheet.scss").decode())
        
            