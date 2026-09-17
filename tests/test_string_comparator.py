import pytest

from StringComparator.string_compare_dataclasses import BinaryLogicEnum, CompareMethodEnum
from StringComparator.string_compare_rules import StringCompareRuleSimple
from StringComparator.string_comparitor import _RULE_DICT_CACHE, get_rule_dict, parse_rule_file


class TestRuleValidation:
    def test_requires_keywords(self):
        with pytest.raises(ValueError):
            StringCompareRuleSimple(method=CompareMethodEnum.CONTAIN, keywords=[])

    def test_requires_logic_for_multiple_keywords(self):
        with pytest.raises(ValueError):
            StringCompareRuleSimple(method=CompareMethodEnum.CONTAIN, keywords=['a', 'b'])

    def test_single_keyword_needs_no_logic(self):
        rule = StringCompareRuleSimple(method=CompareMethodEnum.CONTAIN, keywords=['a'])
        assert rule.logic is None

    def test_str_method_coerced(self):
        rule = StringCompareRuleSimple(method='contain', keywords=['a'])
        assert rule.method == CompareMethodEnum.CONTAIN

    def test_str_logic_coerced(self):
        rule = StringCompareRuleSimple(method='contain', keywords=['a', 'b'], logic='and')
        assert rule.logic == BinaryLogicEnum.AND

    def test_invalid_method(self):
        with pytest.raises(ValueError):
            StringCompareRuleSimple(method=CompareMethodEnum('bogus'), keywords=['a'])


class TestRuleMatching:
    def test_empty_line_raises(self):
        rule = StringCompareRuleSimple(method=CompareMethodEnum.CONTAIN, keywords=['a'])
        with pytest.raises(ValueError):
            rule.matches('')

    def test_contain_single(self):
        rule = StringCompareRuleSimple(method=CompareMethodEnum.CONTAIN, keywords=['Samson'])
        assert rule.matches('Samson is a good man')
        assert not rule.matches('nobody here')

    def test_contain_and(self):
        rule = StringCompareRuleSimple(
            method=CompareMethodEnum.CONTAIN, keywords=['foo', 'bar'], logic=BinaryLogicEnum.AND
        )
        assert rule.matches('foo and bar')
        assert not rule.matches('foo only')

    def test_contain_or(self):
        rule = StringCompareRuleSimple(
            method=CompareMethodEnum.CONTAIN, keywords=['foo', 'bar'], logic=BinaryLogicEnum.OR
        )
        assert rule.matches('just foo')
        assert rule.matches('just bar')
        assert not rule.matches('neither')

    def test_start_with(self):
        rule = StringCompareRuleSimple(method=CompareMethodEnum.START_WITH, keywords=['GET'])
        assert rule.matches('GET /api')
        assert not rule.matches('POST /api')

    def test_end_with(self):
        rule = StringCompareRuleSimple(method=CompareMethodEnum.END_WITH, keywords=['.py'])
        assert rule.matches('main.py')
        assert not rule.matches('main.txt')

    def test_regex_single(self):
        rule = StringCompareRuleSimple(method=CompareMethodEnum.REGEX, keywords=[r'.*?\[Samson.*?'])
        assert rule.matches('[Samson is good')
        assert not rule.matches('no match here')

    def test_regex_and(self):
        rule = StringCompareRuleSimple(
            method=CompareMethodEnum.REGEX, keywords=[r'\d{4}', r'error'], logic=BinaryLogicEnum.AND
        )
        assert rule.matches('2024 error at line 3')
        assert not rule.matches('2024 all good')

    def test_regex_or(self):
        rule = StringCompareRuleSimple(
            method=CompareMethodEnum.REGEX, keywords=[r'^FATAL', r'^ERROR'], logic=BinaryLogicEnum.OR
        )
        assert rule.matches('FATAL: boom')
        assert rule.matches('ERROR: boom')
        assert not rule.matches('WARN: boom')

    def test_unsupported_logic_raises(self):
        rule = StringCompareRuleSimple(
            method=CompareMethodEnum.CONTAIN, keywords=['a', 'b'], logic=object()
        )
        with pytest.raises(NotImplementedError):
            rule.matches('a and b')


class TestRuleFileParsing:
    def test_parse_sample_rules(self):
        data = parse_rule_file()
        assert 'RuleGroup1' in data
        assert 'RuleGroup2' in data
        for group in data.values():
            assert all(isinstance(rule, StringCompareRuleSimple) for rule in group)

    def test_sample_rule_matches(self):
        data = get_rule_dict()
        rg1 = data['RuleGroup1'][0]
        assert rg1.matches('Samson is here')
        assert not rg1.matches('David is here')

    def test_get_rule_dict_caches(self):
        first = get_rule_dict()
        second = get_rule_dict()
        assert first is second

    def test_custom_rule_file(self, tmp_path):
        rule_file = tmp_path / 'rules.toml'
        rule_file.write_text(
            '[[MyGroup]]\n'
            'method = "start_with"\n'
            'keywords = ["BUG"]\n',
            encoding='utf-8',
        )
        data = get_rule_dict(str(rule_file))
        assert list(data.keys()) == ['MyGroup']
        assert data['MyGroup'][0].matches('BUG-001: wobbly wheel')

    def test_custom_rule_file_cached_per_path(self, tmp_path):
        rule_a = tmp_path / 'a.toml'
        rule_b = tmp_path / 'b.toml'
        rule_a.write_text('[[G]]\nmethod = "contain"\nkeywords = ["x"]\n', encoding='utf-8')
        rule_b.write_text('[[G]]\nmethod = "contain"\nkeywords = ["y"]\n', encoding='utf-8')
        data_a = get_rule_dict(str(rule_a))
        data_b = get_rule_dict(str(rule_b))
        assert data_a['G'][0].keywords == ['x']
        assert data_b['G'][0].keywords == ['y']
        # different files must not share the cache entry
        assert _RULE_DICT_CACHE[str(rule_a)] is data_a
        assert _RULE_DICT_CACHE[str(rule_b)] is data_b

    def test_empty_rule_file(self, tmp_path):
        empty = tmp_path / 'empty.toml'
        empty.write_text('', encoding='utf-8')
        assert parse_rule_file(str(empty)) == {}

    def test_malformed_rule_file(self, tmp_path):
        bad = tmp_path / 'bad.toml'
        bad.write_text('[[G]]\nmethod = "contain"\nkeywords = "not-a-list"\n', encoding='utf-8')
        with pytest.raises((TypeError, ValueError)):
            parse_rule_file(str(bad))

    def test_missing_rule_file(self):
        with pytest.raises(FileNotFoundError):
            parse_rule_file('/nonexistent/rules.toml')