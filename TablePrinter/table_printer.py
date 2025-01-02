import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, List, Tuple, TypeVar


@dataclass_json
@dataclass
class BaseRow:
    """
    1. Each instance represent a row of data.
    2. Define a column: Each public field is a column.
        Ex: Col1: int = 1
    3. Provide column alias: column alias is displayed in the table title when printing out the table.
        Each private field that ends with '_alias' is a column alias for display.
        Ex: __Col1_alias: Final[str] = 'Column1AliasName'
    4. Hide column in output: if a column is hidden, it will not show when printing out the table.
        Each private field that ends with '_hide' is a hidden controller for a column.
        Ex: __Col1_hide: Final[bool] = True
    """
    __ALIAS_PREFIX: str = None
    __ALIAS_SUFFIX: str = '_alias'
    __HIDE_PREFIX: str = None
    __HIDE_SUFFIX: str = '_hide'

    __COL_ATTR_NAMES: List[str] = None
    __COL_HEADER_DISP_LEN_MAP: Dict[str, int] = None
    __COL_HEADER_LEN_MAP: Dict[str, int] = None
    __COL_HEADER_MAP: Dict[str, str] = None

    @classmethod
    def __GET_ALIAS_PREFIX(cls):
        if cls.__ALIAS_PREFIX is None:
            cls.__ALIAS_PREFIX = f'_{cls.__name__}__'
        return cls.__ALIAS_PREFIX

    @classmethod
    def __GET_ALIAS_SUFFIX(cls):
        return cls.__ALIAS_SUFFIX
    
    @classmethod
    def __GET_HIDE_PREFIX(cls):
        if cls.__HIDE_PREFIX is None:
            cls.__HIDE_PREFIX = f'_{cls.__name__}__'
        return cls.__HIDE_PREFIX

    @classmethod
    def __GET_HIDE_SUFFIX(cls):
        return cls.__HIDE_SUFFIX

    @classmethod
    def __init_class_col_attributes(cls) -> None:
        cls.__COL_ATTR_NAMES = [
            attr for attr in cls.__annotations__ 
            if not attr.startswith('__') and not cls._is_alias(attr) and not cls._is_hidden_controller(attr)
        ]
        cls.__COL_HEADER_DISP_LEN_MAP = dict()
        cls.__COL_HEADER_LEN_MAP = dict()
        cls.__COL_HEADER_MAP = dict()
        for attr_name in cls.__COL_ATTR_NAMES:
            has_alias, alias_attr = cls._try_get_alias_attr(attr_name)
            col_header = cls.__dict__.get(alias_attr, attr_name) if has_alias else attr_name
            cls.__COL_HEADER_DISP_LEN_MAP[attr_name] = get_display_length(col_header)
            cls.__COL_HEADER_LEN_MAP[attr_name] = len(col_header)
            cls.__COL_HEADER_MAP[attr_name] = col_header

    @classmethod
    def _get_alias_attr_name(cls, col_name: str) -> str:
        """
        Column Alias Naming: _<RowClassName>__<ColumnAttributeName>_alias, where _<RowClassName> is added by 
        python name mangling
        """
        return f'{cls.__GET_ALIAS_PREFIX()}{col_name}{cls.__GET_ALIAS_SUFFIX()}'

    @classmethod
    def _is_alias(cls, attr_name: str) -> bool:
        """ check if the given name is an alias field
        Args:
            attr_name (str): an attribute name
        Returns:
            bool: True if matches alias attribute name pattern
        """
        return attr_name.startswith(cls.__GET_ALIAS_PREFIX()) and attr_name.endswith(cls.__GET_ALIAS_SUFFIX())

    @classmethod
    def _is_hidden_controller(cls, attr_name: str) -> bool:
        """ check if the given name is a hidden controller field
        Returns:
            bool: True if matches hidden controller attribute name pattern
        """
        return attr_name.startswith(cls.__GET_HIDE_PREFIX()) and attr_name.endswith(cls.__GET_HIDE_SUFFIX())

    @classmethod
    def _try_get_alias_attr(cls, attr_name: str) -> Tuple[bool, str]:
        """ try to get the alias attribute name of the given attribute name
        Args:
            attr_name (str): an attribute name
        Returns:
            Tuple[bool, str]: 
                if alias attribute is defined, return True and the alias attribute namem
                if alias attribute is not defined, return False and blank string
        """
        if cls._is_alias(attr_name):
            # given attribute itself is an alias
            return False, ''

        alias_attr = cls._get_alias_attr_name(attr_name)
        if alias_attr in cls.__annotations__:
            # alias attribute is defined
            return True, alias_attr
        # alias attribute is not defined
        return False, ''

    @classmethod
    def get_col_attr_names(cls) -> List[str]:
        """ return the list of all column attribute names (no alias, just attribute names) """
        if cls.__COL_ATTR_NAMES is None:
            cls.__init_class_col_attributes()
        return cls.__COL_ATTR_NAMES

    @classmethod
    def get_col_header_disp_len_map(cls) -> Dict[str, int]:
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

    def get_col_value_disp_len(self) -> Dict[str, int]:
        """return the map between column attribute name and column content display length
        Returns:
            Dict[str, int]: key: column_attribute_name: value: column display length when cast to string type
        """
        # print(f'{BaseRow.__name__}.{self.get_col_value_width.__name__}', self.__annotations__)
        ret = dict()
        for attr_name in self.get_col_attr_names():
            ret[attr_name] = get_display_length(str(self.__getattribute__(attr_name)))
        return ret

    @classmethod
    def get_col_header_len_map(cls) -> Dict[str, int]:
        """ return the map between column attribute name and column header length
        Returns:
            Dict[str, int]: key: column_attribute_name; value: length of column alias if defined else column_attribute_name
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


TBaseRow = TypeVar('TBaseRow', bound=BaseRow)


class BaseTable:
    row_type: TBaseRow = BaseRow
    CHAR_LN: str = ''
    CHAR_COL_SEP: str = '|'
    CHAR_ROW_SEP: str = ''

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

    def get_table_header_str(self) -> str:
        """ generate the header line for the output table """
        # print(f'{self.__class__.__name__}.{self.get_table_header_str.__name__} row_type:{self.row_type}')
        col_order = self.row_type.get_col_attr_names()
        col_data = [self.row_type.get_col_header_map()[attr] for attr in col_order]
        col_disp_len = [self.__COL_MAX_DISP_LEN[attr] for attr in col_order]
        ret = f' {self.CHAR_COL_SEP} '.join(
            f'{col_val:^{width-get_display_length(str(col_val))+len(str(col_val))}}'
            for col_val, width in zip(col_data, col_disp_len)
        )
        return ret

    def get_table_header_sep_str(self) -> str:
        """ generate the header separator line for the output table """
        col_order = self.row_type.get_col_attr_names()
        col_data = ['-' * self.__COL_MAX_DISP_LEN[attr] for attr in col_order]
        col_disp_len = [self.__COL_MAX_DISP_LEN[attr] for attr in col_order]
        ret = f'-{self.CHAR_COL_SEP}-'.join(
            f'{col_val:^{width-get_display_length(str(col_val))+len(str(col_val))}}'
            for col_val, width in zip(col_data, col_disp_len)
        )
        return ret

    def get_table_line_str(self, row_data: TBaseRow) -> str:
        """ generate a row line of the given row_data for the output table """
        col_order = self.row_type.get_col_attr_names()
        col_data = [row_data.__getattribute__(attr) for attr in col_order]
        col_disp_len = [self.__COL_MAX_DISP_LEN[attr] for attr in col_order]
        ret = f' {self.CHAR_COL_SEP} '.join(
            f'{col_val:^{width-get_display_length(str(col_val))+len(str(col_val))}}' 
            for col_val, width in zip(col_data, col_disp_len)
        )
        return ret

    def insert_row(self, row_data: TBaseRow):
        """ insert a row_data in to the row_list """
        if not isinstance(row_data, self.row_type):
            raise TypeError(f'row_data type: {type(row_data)} does not match {self.row_type}')
        self.row_list.append(row_data)
        self._update_col_max_disp_len(row_data=row_data)

    def print_table(self):
        # print(f'{self.__class__.__name__}.{self.to_table_str.__name__} data_len:{len(self.row_list)}')
        output_lines: List[str] = [self.get_table_header_str(), self.get_table_header_sep_str()]
        for row_data in self.row_list:
            output_lines.append(self.get_table_line_str(row_data))
        for l in output_lines:
            print(l)


def get_display_length(s: str) -> int:
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
