import os
import tomllib
from typing import Dict, List

from StringComparator.string_compare_rules import StringCompareRuleSimple

PATH_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PATH_RULE = os.path.join(PATH_SCRIPT, 'data/sample_rules.toml')

# Per-path cache: keyed by the rule file path so multiple rule files can be
# loaded and used side by side without cross-contamination.
_RULE_DICT_CACHE: Dict[str, Dict[str, List[StringCompareRuleSimple]]] = {}


def parse_rule_file(path: str = PATH_RULE) -> Dict[str, List[StringCompareRuleSimple]]:
    """Parse a TOML rule file into {rule_group_name: [StringCompareRuleSimple, ...]}.

    The file must be an array-of-tables TOML document where each top-level
    table (e.g. ``[[RuleGroupName]]``) is a list of rule dicts, each matching
    the fields of :class:`StringCompareRuleSimple`.

    Args:
        path: Path of the TOML rule file. Defaults to the bundled
            ``data/sample_rules.toml``.
    """
    with open(path, 'rb') as f_in:
        data = tomllib.load(f_in)
        if not data:
            return {}
        for rule_group_name, rule_group in data.items():
            if not isinstance(rule_group, list):
                raise ValueError(
                    f'rule group {rule_group_name!r} must be an array of tables in {path}, '
                    f'got {type(rule_group).__name__}'
                )
            if not rule_group:
                continue
            rule_objs = []
            for rule in rule_group:
                try:
                    rule_objs.append(StringCompareRuleSimple(**rule))
                except (TypeError, ValueError) as e:
                    raise type(e)(
                        f'invalid rule in group {rule_group_name!r} of {path}: {rule!r} ({e})'
                    ) from e
            data[rule_group_name] = rule_objs
        return data


def get_rule_dict(path: str = PATH_RULE) -> Dict[str, List[StringCompareRuleSimple]]:
    """Return the parsed rule dict for ``path``, cached after the first parse.

    Args:
        path: Path of the TOML rule file. Defaults to the bundled
            ``data/sample_rules.toml``.
    """
    if path not in _RULE_DICT_CACHE:
        _RULE_DICT_CACHE[path] = parse_rule_file(path)
    return _RULE_DICT_CACHE[path]