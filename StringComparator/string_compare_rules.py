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

    def matches(self, line: str) -> bool:
        if not line:
            raise ValueError('line cannot be empty')

        if self.method == CompareMethodEnum.CONTAIN:
            if not self.logic:
                return self.keywords[0] in line
            elif self.logic == BinaryLogicEnum.AND:
                return all(keyword in line for keyword in self.keywords)
            elif self.logic == BinaryLogicEnum.OR:
                return any(keyword in line for keyword in self.keywords)
            else:
                raise NotImplementedError(f'compare_method={self.method} compare_rule={self.logic} is not supported')

        elif self.method == CompareMethodEnum.START_WITH:
            if not self.logic:
                return line.startswith(self.keywords[0])
            elif self.logic == BinaryLogicEnum.AND:
                return all(line.startswith(keyword) for keyword in self.keywords)
            elif self.logic == BinaryLogicEnum.OR:
                return any(line.startswith(keyword) for keyword in self.keywords)
            else:
                raise NotImplementedError(f'compare_method={self.method} compare_rule={self.logic} is not supported')

        elif self.method == CompareMethodEnum.END_WITH:
            if not self.logic:
                return line.endswith(self.keywords[0])
            elif self.logic == BinaryLogicEnum.AND:
                return all(line.endswith(keyword) for keyword in self.keywords)
            elif self.logic == BinaryLogicEnum.OR:
                return any(line.endswith(keyword) for keyword in self.keywords)
            else:
                raise NotImplementedError(f'compare_method={self.method} compare_rule={self.logic} is not supported')

        elif self.method == CompareMethodEnum.REGEX:
            if not self.logic:
                return bool(re.search(self.keywords[0], line))
            elif self.logic == BinaryLogicEnum.AND:
                return all(re.search(keyword, line) for keyword in self.keywords)
            elif self.logic == BinaryLogicEnum.OR:
                return any(re.search(keyword, line) for keyword in self.keywords)
            else:
                raise NotImplementedError(f'compare_method={self.method} compare_rule={self.logic} is not supported')

        else:
            raise NotImplementedError(f'compare_method={self.method} is not supported')
