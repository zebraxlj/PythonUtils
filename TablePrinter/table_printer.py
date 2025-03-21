import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, TypeVar

from ColorHelper.color_xterm_256 import ColorXTerm256


class ColumnAlignment(str, Enum):
    CENTER = '^'
    LEFT = '<'
    RIGHT = '>'

    def __str__(self):
        return self.value


@dataclass
class FontFormat:
    BgColor: ColorXTerm256 = None
    FgColor: ColorXTerm256 = None

    def apply_format(self, text: str) -> str:
        if isinstance(self.BgColor, ColorXTerm256):
            text = f'\033[;48;5;{self.BgColor}m{text}\033[0m'
        if isinstance(self.FgColor, ColorXTerm256):
            text = f'\033[;38;5;{self.FgColor}m{text}\033[0m'
        return text


@dataclass
class ConditionalFormat:
    format: FontFormat = field(
        default_factory=lambda: FontFormat(BgColor=ColorXTerm256.RED, FgColor=ColorXTerm256.WHITE)
    )

    def apply_format(self, text: str) -> str:
        raise NotImplementedError

    def is_condition_match(self, text: str):
        raise NotImplementedError


@dataclass
class CondFmtContain(ConditionalFormat):
    contain_target: str = None

    def apply_format(self, text: any) -> str:
        return self.format.apply_format(text)
        text = str(text)
        return f"\033[;48;5;{ColorXTerm256.RED}m{text}\033[0m"
        len_space_l = len(text) - len(text.lstrip())
        len_space_r = len(text) - len(text.rstrip())
        return f'{"*" * len_space_l}{text.strip()}{"*" * len_space_r}'

    def is_condition_match(self, text: str):
        if self.contain_target is None:
            raise ValueError('contain_target is not defined')
        return self.contain_target in text


@dataclass
class CondFmtExactMatch(ConditionalFormat):
    match_target: str = None

    def apply_format(self, text: any) -> str:
        return self.format.apply_format(text)
        text = str(text)
        len_space_l = text.index(self.match_target)
        len_space_r = len(text) - len_space_l - len(self.match_target)
        return f'{"*" * len_space_l}{self.match_target}{"*" * len_space_r}'

    def is_condition_match(self, text: str):
        if self.match_target is None:
            raise ValueError('match_target is not defined')
        return text == self.match_target


TConditionalFormat = TypeVar('TConditionalFormat', bound=ConditionalFormat)


@dataclass
class ColumnConfig:
    """ define the property of a column.

    Attributes:
        alias: column alias is displayed in the table title when printing out the table.
        format: if a column holds datetime data, output table print the value regarding to the format.
        hide: if a column is hidden, it will not show when printing out the table.
    """
    alias: Optional[str] = None

    align: Optional[ColumnAlignment] = ColumnAlignment.CENTER

    conditional_format: Optional[TConditionalFormat] = None

    format: Optional[str] = None

    hide: Optional[bool] = None


@dataclass
class BaseRow:
    """
    1. Each instance represent a row of data.
    2. Define a column: Each public field is a column.
        Ex: Col1: int = 1
    3. Provide column config: type: ColumnConfig
        Ex: __Col1_config: Final[ColumnConfig] = ColumnConfig(alias="Column1")
    """
    __CONFIG_PREFIX: str = None
    __CONFIG_SUFFIX: str = '_config'

    __COL_ATTR_NAMES: List[str] = None
    __COL_HEADER_DISP_LEN_MAP: Dict[str, int] = None
    __COL_HEADER_LEN_MAP: Dict[str, int] = None
    __COL_HEADER_MAP: Dict[str, str] = None

    @classmethod
    def __GET_CONFIG_PREFIX(cls):
        if cls.__CONFIG_PREFIX is None:
            cls.__CONFIG_PREFIX = f'_{cls.__name__}__'
        return cls.__CONFIG_PREFIX

    @classmethod
    def __GET_CONFIG_SUFFIX(cls):
        return cls.__CONFIG_SUFFIX

    @classmethod
    def __init_class_col_attributes(cls) -> None:
        cls.__COL_ATTR_NAMES = [
            attr for attr in cls.__annotations__
            if not attr.startswith('__') and cls._is_col_data_attr(attr) and not cls._is_col_hidden(attr)
        ]
        cls.__COL_HEADER_DISP_LEN_MAP = dict()
        cls.__COL_HEADER_LEN_MAP = dict()
        cls.__COL_HEADER_MAP = dict()
        for attr_name in cls.__COL_ATTR_NAMES:
            col_config: ColumnConfig = cls.get_config(attr_name)
            col_header = col_config.alias if col_config.alias else attr_name
            cls.__COL_HEADER_DISP_LEN_MAP[attr_name] = get_display_length(col_header)
            cls.__COL_HEADER_LEN_MAP[attr_name] = len(col_header)
            cls.__COL_HEADER_MAP[attr_name] = col_header

    @classmethod
    def _get_config_attr_name(cls, col_name: str) -> str:
        """
        Column Config Naming: _<RowClassName>__<ColumnAttributeName>_config, where _<RowClassName> is added by
        python name mangling
        """
        return f'{cls.__GET_CONFIG_PREFIX()}{col_name}{cls.__GET_CONFIG_SUFFIX()}'

    @classmethod
    def _is_col_data_attr(cls, attr_name: str) -> bool:
        """ check if the given name is the attribute that holds the column value
        Args:
            attr_name (str): an attribute name
        Returns:
            bool: True if attribute is not config
        """
        return (
            not cls._is_config(attr_name)
        )

    @classmethod
    def _is_config(cls, attr_name: str) -> bool:
        """ check if the given name is an config field
        Args:
            attr_name (str): an attribute name
        Returns:
            bool: True if matches config attribute name pattern
        """
        return attr_name.startswith(cls.__GET_CONFIG_PREFIX()) and attr_name.endswith(cls.__GET_CONFIG_SUFFIX())

    @classmethod
    def _is_col_hidden(cls, attr_name: str) -> bool:
        """check if the given name is an attribute that's hidden by its hidden controller
        Returns:
            bool: True if hidden controller exists and is set to True
        """
        if not cls._is_col_data_attr(attr_name):
            return False
        col_config: ColumnConfig = cls.get_config(attr_name)
        if col_config.hide:
            return True
        return False

    @classmethod
    def get_col_attr_names(cls) -> List[str]:
        """ return the list of all column attribute names (no config, just attribute names) """
        if cls.__COL_ATTR_NAMES is None:
            cls.__init_class_col_attributes()
        return cls.__COL_ATTR_NAMES

    @classmethod
    def get_col_header_disp_len_map(cls) -> Dict[str, int]:
        """ return the map between column attribute name and column header display length
        Returns:
            Dict[str, int]: key: column_attribute_name; value: column header display length
        """
        if cls.__COL_HEADER_DISP_LEN_MAP is None:
            cls.__init_class_col_attributes()
        return cls.__COL_HEADER_DISP_LEN_MAP

    @classmethod
    def get_col_header_map(cls) -> Dict[str, str]:
        """ return the map between column attribute name and column header name
        Returns:
            Dict[str, str]: key: column_attribute_name; value: column alias name if defined else column_attribute_name
        """
        if cls.__COL_HEADER_MAP is None:
            cls.__init_class_col_attributes()
        return cls.__COL_HEADER_MAP

    def get_col_value_disp(self) -> Dict[str, int]:
        """ return the map between column attribute name and column formatted content
        Returns:
            Dict[str, int]:
                key: column_attribute_name
                value: formatted column content if format is provided; otherwise, original content
        """
        ret = dict()
        for attr_name in self.get_col_attr_names():
            attr_val = self.__getattribute__(attr_name)
            if isinstance(attr_val, datetime):
                col_config: ColumnConfig = self.get_config(attr_name)
                if col_config.format:
                    ret[attr_name] = attr_val.strftime(col_config.format)
                    continue
            ret[attr_name] = self.__getattribute__(attr_name)
        return ret

    def get_col_value_disp_len(self) -> Dict[str, int]:
        """return the map between column attribute name and column content display length
        Returns:
            Dict[str, int]: key: column_attribute_name: value: column display length when cast to string type
        """
        # print(f'{BaseRow.__name__}.{self.get_col_value_width.__name__}', self.__annotations__)
        ret = dict()
        col_value_disp: dict = self.get_col_value_disp()
        for attr_name in self.get_col_attr_names():
            ret[attr_name] = get_display_length(str(col_value_disp[attr_name]))
        return ret

    @classmethod
    def get_col_header_len_map(cls) -> Dict[str, int]:
        """ return the map between column attribute name and column header length
        Returns:
            Dict[str, int]:
                key: column_attribute_name;
                value: length of column alias if defined else column_attribute_name
        """
        if cls.__COL_HEADER_LEN_MAP is None:
            cls.__init_class_col_attributes()
        return cls.__COL_HEADER_LEN_MAP

    def get_col_value_len(self) -> Dict[str, int]:
        """ return the map between column attribute name and column value length
        Returns:
            Dict[str, int]: key: column_attribute_name; value: length of column value when casted to str
        """
        ret = dict()
        for attr_name in self.get_col_attr_names():
            ret[attr_name] = len(str(self.__getattribute__(attr_name)))
        return ret

    @classmethod
    def is_col_attr_exist(cls, attr_name: str) -> bool:
        """ check if attr_name is a column attribute defined in row_type """
        return (
            attr_name in cls.__annotations__  # attr_name is defined
            and cls._is_col_data_attr(attr_name)  # attribute with attr_name holds actual data
        )

    @classmethod
    def get_config(cls, attr_name: str) -> ColumnConfig:
        """get config of the given attribute name if defined, else return the default ColumnConfig()

        Args:
            attr_name (str): an attribute name

        Raises:
            ValueError: when given attr_name doesn't hold data
        """
        if not cls._is_col_data_attr(attr_name):
            # given attribute doesn't hold column data
            raise ValueError(f'Cannot get config on non-data attribute: {attr_name}.')

        config_attr_name = cls._get_config_attr_name(attr_name)
        if config_attr_name in cls.__dict__:
            # config attribute is defined
            return cls.__dict__[config_attr_name]
        # config attribute is not defined, return default ColumnConfig
        return ColumnConfig()


TBaseRow = TypeVar('TBaseRow', bound=BaseRow)


class BaseTable:
    row_type: TBaseRow = BaseRow
    CHAR_LN: str = '\r\n'
    CHAR_COL_SEP: str = '\u2502'
    CHAR_ROW_SEP: str = '\u2500'
    CHAR_HEADER_H_SEP: str = '\u2550'
    CHAR_HEADER_V_SEP: str = '\u256a'

    def __init__(self, *args, **kwargs):
        self.__COL_MAX_DISP_LEN: defaultdict = defaultdict(int)
        self.__COL_MAX_LEN: defaultdict = defaultdict(int)
        for attr_name, header_width in self.row_type.get_col_header_len_map().items():
            self.__COL_MAX_LEN[attr_name] = header_width
        for attr_name, header_disp_len in self.row_type.get_col_header_disp_len_map().items():
            self.__COL_MAX_DISP_LEN[attr_name] = header_disp_len
        self.row_list: List[TBaseRow] = []

    def _get_col_max_disp_len(self) -> Dict[str, int]:
        """ 用于测试 self.__COL_MAX_DISP_LEN """
        # d: BaseRow
        # get max width for each column
        col_max_disp_len: Dict[str, int] = defaultdict(lambda: 0)
        for d in self.row_list:
            for col, width in d.get_col_value_disp_len().items():
                col_max_disp_len[col] = max(col_max_disp_len[col], width)
        # print(f'{self.__class__.__name__}.{self.get_col_max_width.__name__} col_max_width:{col_max_width}')
        return col_max_disp_len

    def _update_col_max_disp_len(self, row_data: TBaseRow) -> None:
        for col, disp_len in row_data.get_col_value_disp_len().items():
            self.__COL_MAX_DISP_LEN[col] = max(self.__COL_MAX_DISP_LEN[col], disp_len)

    def _update_col_max_len(self, row_data: TBaseRow) -> None:
        """ update the self.__COL_MAX_LEN if any attribute in the row_data is longer than record
        Args:
            row_data (TBaseRow): used to
        """
        for col, val_len in row_data.get_col_value_len().items():
            self.__COL_MAX_LEN[col] = max(self.__COL_MAX_LEN[col], val_len)

    def get_sorted_rows(self, order_by: List[str], ascending: List[bool] = None) -> List[TBaseRow]:
        """ return the sorted row list of the current table
        Args:
            order_by (List[str]):
                order_by is used to sort the result-set in ascending or descending order.
                All elements in order_by requires to be a column attribute name defined in row_type.
                The sorting effect is equivalent to sql's order by clause.
                Records are sorted in ascending order by default. To sort in descending order, use the ascending param.
            ascending (List[bool], optional):
                List of true false that marks whether the column in order_by is sorted in ascending or descending order.
                If provided, order_by needs to be provided and having the same length.
                If not provided, all columns will be sorted in ascending order.
        Raises:
            ValueError: when order_by is not defined, empty, or contain undefined attribute names
            ValueError: when ascending is passed but having different length comparing to order_by
            ValueError: when ascending is passed but order_by is not
        Returns:
            List[TBaseRow]: sorted row list
        """
        if not order_by:
            raise ValueError(f'invalid order_by: {order_by}')

        # validate attribute names in order_by
        attr_names_bad = [attr_name for attr_name in order_by if not self.row_type.is_col_attr_exist(attr_name)]
        if attr_names_bad:
            raise ValueError(f'Unknown attribute names in order_by: {attr_names_bad}')

        # default sorting order is ascending
        ascending = [True] * len(order_by) if not ascending else ascending
        # validate ascending length
        if len(order_by) != len(ascending):
            raise ValueError('order_by and ascending should have the same length when both are passed in')

        ret = self.row_list

        # sort data
        if order_by:
            is_all_asc: bool = all(ascending)
            is_all_desc: bool = all(not asc for asc in ascending)
            if is_all_asc or is_all_desc:
                # sorting order is all ascending or decending
                ret = sorted(
                    ret,
                    key=lambda row_data: [row_data.__getattribute__(attr_name) for attr_name in order_by],
                    reverse=True if is_all_desc else False,
                )
            else:
                # according to https://docs.python.org/3/howto/sorting.html, sort is stable.
                # When multiple records have the same key, their original order is preserved.
                for attr_name, asc in zip(order_by[::-1], ascending[::-1]):
                    ret = sorted(
                        ret, key=lambda row_data: row_data.__getattribute__(attr_name), reverse=not asc
                    )
        elif ascending:
            raise ValueError('ascending should not be passed without order_by')

        return ret

    def get_table_header_str(self) -> str:
        """ generate the header line for the output table """
        # print(f'{self.__class__.__name__}.{self.get_table_header_str.__name__} row_type:{self.row_type}')
        col_order = self.row_type.get_col_attr_names()
        col_align = [self.row_type.get_config(attr).align for attr in col_order]
        col_data = [self.row_type.get_col_header_map()[attr] for attr in col_order]
        col_disp_len = [self.__COL_MAX_DISP_LEN[attr] for attr in col_order]
        ret = self.CHAR_COL_SEP.join(
            f' {col_val:{align}{width-get_display_length(str(col_val))+len(str(col_val))}} '
            for col_val, align, width in zip(col_data, col_align, col_disp_len)
        )
        return ret

    def get_table_header_sep_str(self, sep_h: str = None, sep_v: str = None) -> str:
        """ generate the header separator line for the output table
        Args:
            sep_h (str, optional): horrizontal separater
            sep_v (str, optional): vertical separater
        Returns:
            str: header separator line
        """
        sep_h = sep_h if sep_h else self.CHAR_HEADER_H_SEP
        sep_v = sep_v if sep_v else self.CHAR_HEADER_V_SEP
        return self.get_table_line_sep_str(sep_h=sep_h, sep_v=sep_v)

    def get_table_line_sep_str(self, sep_h: str = None, sep_v: str = None, dense: bool = True) -> str:
        """ generate row separator line for the output table
        Args:
            sep_h (str, optional): horrizontal separater. Defaults to None.
            sep_v (str, optional): vertical separater. Defaults to None.
            dense (bool, optional):
                When True there'll be no space between row sep_h and column sep_v Ex. ----|----.
                When False there'll be a space between row sep_h and column sep_v Ex. --- | ---.
                Defaults to True.
        Returns:
            str: row separator line
        """
        sep_h = sep_h if sep_h else self.CHAR_ROW_SEP
        sep_v = sep_v if sep_v else self.CHAR_COL_SEP
        col_order = self.row_type.get_col_attr_names()
        col_align = [self.row_type.get_config(attr).align for attr in col_order]
        col_data = [sep_h * self.__COL_MAX_DISP_LEN[attr] for attr in col_order]
        col_disp_len = [self.__COL_MAX_DISP_LEN[attr] for attr in col_order]
        col_pad = sep_h if dense else ' '
        col_sep = sep_v
        ret = col_sep.join(
            f'{col_pad}{col_val:{align}{width-get_display_length(str(col_val))+len(str(col_val))}}{col_pad}'
            for col_val, align, width in zip(col_data, col_align, col_disp_len)
        )
        return ret

    def get_table_line_str(self, row_data: TBaseRow) -> str:
        """ generate a row line of the given row_data for the output table """
        col_order = self.row_type.get_col_attr_names()
        col_config = [self.row_type.get_config(attr) for attr in col_order]
        col_data_disp = row_data.get_col_value_disp()
        col_data = [col_data_disp[attr] for attr in col_order]
        col_disp_len = [self.__COL_MAX_DISP_LEN[attr] for attr in col_order]

        tokens = []
        for text, config, width in zip(col_data, col_config, col_disp_len):
            need_conf_fmt = config.conditional_format is not None and config.conditional_format.is_condition_match(text)
            text = f' {str(text):{config.align}{width-get_display_length(str(text))+len(str(text))}} '
            if need_conf_fmt:
                text = config.conditional_format.apply_format(text)
            tokens.append(text)
        return self.CHAR_COL_SEP.join(tokens)

    def insert_row(self, row_data: TBaseRow):
        """ insert a row_data in to the row_list """
        if type(row_data) is not self.row_type:
            raise TypeError(f'row_data type: {type(row_data)} does not match {self.row_type}')
        self.row_list.append(row_data)
        self._update_col_max_disp_len(row_data=row_data)

    def print_table(self, order_by: List[str] = None, ascending: List[bool] = None):
        """print the table
        Args:
            order_by (List[str], optional): see order_by in get_sorted_rows
            ascending (List[bool], optional): see ascending in get_sorted_rows
        """
        # print(f'{self.__class__.__name__}.{self.to_table_str.__name__} data_len:{len(self.row_list)}')
        output_lines: List[str] = [self.get_table_header_str(), self.get_table_header_sep_str()]

        data_to_show = self.row_list if not order_by else self.get_sorted_rows(order_by, ascending)

        for row_data in data_to_show:
            output_lines.append(self.get_table_line_str(row_data))

        output_str = self.CHAR_LN.join(output_lines)
        print(output_str, '\n', sep='')


def get_display_length(s: str) -> int:
    """ return the display length of the given string. Any wide characters in the input string takes 2 spaces """
    length = 0
    for char in s:
        # Get the Unicode character category
        category = unicodedata.category(char)
        # Check for wide characters
        if category in ('Lo'):
            length += 2  # Wide characters take 2 spaces
        else:
            length += 1  # Narrow characters take 1 space
    return length
