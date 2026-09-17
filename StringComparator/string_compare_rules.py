import re
from dataclasses import dataclass
from typing import List, Optional

from StringComparator.string_compare_dataclasses import BinaryLogicEnum, CompareMethodEnum


@dataclass
class StringCompareRuleSimple:
    method: CompareMethodEnum
    keywords: List[str]
    logic: Optional[BinaryLogicEnum] = None

    def __post_init__(self):
        if not self.keywords:
            raise ValueError('compare_keywords cannot be empty')
        if len(self.keywords) > 1 and not self.logic:
            raise ValueError('compare_rule is required when len(self.compare_keywords) > 1')
        if isinstance(self.method, str):
            self.method = CompareMethodEnum(self.method)
        if isinstance(self.logic, str):
            self.logic = BinaryLogicEnum(self.logic)

    def _keyword_matches(self, line: str, keyword: str) -> bool:
        """Test a single keyword against the line using this rule's compare method."""
        if self.method == CompareMethodEnum.CONTAIN:
            return keyword in line
        if self.method == CompareMethodEnum.START_WITH:
            return line.startswith(keyword)
        if self.method == CompareMethodEnum.END_WITH:
            return line.endswith(keyword)
        if self.method == CompareMethodEnum.REGEX:
            return re.search(keyword, line) is not None
        raise NotImplementedError(f'compare_method={self.method} is not supported')

    def matches(self, line: str) -> bool:
        if not line:
            raise ValueError('line cannot be empty')

        if not self.logic:
            return self._keyword_matches(line, self.keywords[0])
        if self.logic == BinaryLogicEnum.AND:
            return all(self._keyword_matches(line, keyword) for keyword in self.keywords)
        if self.logic == BinaryLogicEnum.OR:
            return any(self._keyword_matches(line, keyword) for keyword in self.keywords)
        raise NotImplementedError(f'compare_method={self.method} compare_rule={self.logic} is not supported')
