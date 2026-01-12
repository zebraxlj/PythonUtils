import sys
from pathlib import Path

PROJ_PATH = str(Path(__file__).resolve().parent.parent)
if PROJ_PATH not in sys.path:
    sys.path.insert(0, PROJ_PATH)

from StringComparator.string_compare_dataclasses import CompareMethodEnum  # noqa: E402
from StringComparator.string_compare_rules import StringCompareRuleSimple  # noqa: E402


def test_StringCompareRuleSimple():
    tmp_rule = StringCompareRuleSimple(
        method=CompareMethodEnum.CONTAIN,
        keywords=['Samson'],
    )
    print(tmp_rule.matches('Samson is a good man'))


def test_string_comparator():
    from StringComparator.string_comparitor import get_rule_dict, parse_rule_file
    data = parse_rule_file()
    print(data)

    for rule_group_name, rules in get_rule_dict().items():
        for rule in rules:
            print(f'{rule_group_name} {rule} {rule.matches("[samson is good")}')
            print(f'{rule_group_name} {rule} {rule.matches("padding [samson is good")}')


if __name__ == '__main__':
    test_StringCompareRuleSimple()
    test_string_comparator()
