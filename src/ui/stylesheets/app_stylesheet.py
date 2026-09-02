from collections import deque
from copy import deepcopy
import pkgutil
import pathlib
from typing import Dict, List, Optional

import sass
import tinycss2

from tinycss2 import ast

from src.utils.singleton import Singleton


class StylesheetRule:
    def __init__(self):
        self.rule: list[ast.QualifiedRule] = []
        self.rules_for_children: Dict[str, StylesheetRule] = {}


def remove_whitespace(node_list: List[ast.Node]):
    """
        Remove WhitespaceToken in node_list
    """
    return [p for p in node_list if not isinstance(p, ast.WhitespaceToken)]

def convert_rules_to_string(qualified_rules: List[ast.QualifiedRule]):
    """
        Convert list of rules to final string    
    """
    return " ".join([rule.serialize().replace("/**/", " ") for rule in qualified_rules])

class StylesheetManager():
    """
        if `load_path` arg is not supplied, it uses `stylesheet.scss` in the same directory
        Load path is used for testing.

        If data is None, loads `load_path`
    """
    def __init__(self, load_path: Optional[pathlib.Path] = None, data: Optional[str] = None):
        self.__root_rule: StylesheetRule = StylesheetRule()
        
        if data is None:
            if load_path is None:
                raise ValueError("Both arguments are None.")
            with open(load_path, encoding="utf-8") as scss:
                data = scss.read()

        qss: str = sass.compile(string=data) # type: ignore
        stylesheet = tinycss2.parse_stylesheet(qss, skip_comments=True, skip_whitespace=True)
        for rule in stylesheet:
            if isinstance(rule, ast.QualifiedRule):
                key = tinycss2.serialize(rule.prelude).strip()
                rule_copy = deepcopy(rule)
                rule_copy.prelude = remove_whitespace(rule_copy.prelude)
                rule_copy.content = remove_whitespace(rule_copy.content)
                cur_rule = self.__root_rule
                final_elems = []
                for elem in key.split(" "):
                    first_separator_index = [
                        ind for ind in
                        (elem.find(sep) for sep in ["#", "::", ":"])
                        if ind != -1
                    ]
                    first_separator_index = min(first_separator_index) if first_separator_index else None
                    
                    if first_separator_index is not None:
                        elem = elem[:first_separator_index]
                        
                    if elem not in cur_rule.rules_for_children:
                        cur_rule.rules_for_children[elem] = StylesheetRule()
                    cur_rule = cur_rule.rules_for_children[elem]
                    final_elems.append(elem)
                cur_rule.rule.append(rule_copy)

    def get_rule(self, selector: str, return_universals_even_if_not_found = False) -> Optional[str]:
        """
            Get rule from selectors

            Returns None when there isn't available

            Is sorted by increasing specificity, e.g. 'a b c' is placed later than 'a b'
        """
        cur_rule = self.__root_rule
        qualified_rules: list[ast.QualifiedRule] = []
        last_elem = None
        for elem in selector.split(" "):
            try:
                if child := cur_rule.rules_for_children.get("*", None):
                    qualified_rules.extend(child.rule)

                cur_rule = cur_rule.rules_for_children[elem]
            except KeyError:
                if return_universals_even_if_not_found:
                    return convert_rules_to_string(qualified_rules)
                return None
            last_elem = elem
        if last_elem is not None and last_elem == "*":
            return convert_rules_to_string(qualified_rules)
        rule_queue = deque([cur_rule])
        while rule_queue:
            cur_qrule = rule_queue.popleft()
            if cur_qrule.rule is not None:
                qualified_rules.extend(cur_qrule.rule)
                
            for v in cur_qrule.rules_for_children.values():
                rule_queue.append(v)

        return convert_rules_to_string(qualified_rules)


class MainStylesheetManager(StylesheetManager, metaclass=Singleton):
    """
        A version of StylesheetManager that is a singleton automatically loads stylesheet.scss
    """
    def __init__(self):
        data = pkgutil.get_data("src.ui.stylesheets", "app_stylesheet.scss")

        if data is None:
            raise FileNotFoundError("Neighboring stylesheet.scss not found")
        super().__init__(data=data.decode())
        
            