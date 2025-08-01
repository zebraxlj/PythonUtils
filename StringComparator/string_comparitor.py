import os
import tomllib
from typing import Dict, List, Optional

from StringComparator.string_compare_rules import StringCompareRuleSimple


PATH_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PATH_RULE = os.path.join(PATH_SCRIPT, 'data/sample_rules.toml')

RULE_DICT: Optional[Dict[str, List[StringCompareRuleSimple]]] = None


def get_rule_dict() -> Dict[str, List[StringCompareRuleSimple]]:
    global RULE_DICT
    if RULE_DICT is None:
        RULE_DICT = parse_rule_file()
    return RULE_DICT


def parse_rule_file() -> Dict[str, List[StringCompareRuleSimple]]:
    with open(PATH_RULE, 'rb') as f_in:
        data = tomllib.load(f_in)
        if not data:
            return {}
        for rule_group_name, rule_group in data.items():
            if not rule_group:
                continue
            rule_objs = []
            for rule in rule_group:
                rule_objs.append(StringCompareRuleSimple(**rule))
            data[rule_group_name] = rule_objs
        return data
