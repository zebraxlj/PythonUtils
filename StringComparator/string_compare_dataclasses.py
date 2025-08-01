from enum import Enum


class CaseInsensitiveEnum(Enum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class BinaryLogicEnum(CaseInsensitiveEnum):
    AND = 'and'
    OR = 'or'


class CompareMethodEnum(CaseInsensitiveEnum):
    CONTAIN = 'contain'
    END_WITH = 'end_with'
    REGEX = 'regex'
    START_WITH = 'start_with'
