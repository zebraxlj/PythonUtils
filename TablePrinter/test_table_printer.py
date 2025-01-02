from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

from table_printer import BaseRow, BaseTable, get_display_length


@dataclass
class RowExample(BaseRow):
    """
    1. Every field is a column in the row. When define, a default value is required
    2. __<ColumnName>_alias: if defined, it will be used as the alias of the column in the output; otherwise, <ColumnName> will be used
    3. __<ColumnName>_hide: if defined and value is set to True, column will not show up in the output.
    """
    ColInt: int = -1
    # __ColInt_hide: Final[bool] = True

    ColStr: str = 'N/A'
    __ColStr_alias: Final[str] = 'EN column alias'  # test en alias display
    # __ColStr_hide: Final[bool] = True

    ColStrCn: str = 'N/A'
    __ColStrCn_alias: Final[str] = '中文别名'  # test cn alias display
    # __ColStrCn_hide: Final[bool] = True

    LastModifiedDate: datetime = field(default_factory=datetime.now)  # test datetime column display
    # __LastModifiedDate_alias: Final[str] = '最后修改日期'
    # __LastModifiedDate_hide: Final[bool] = True
    __LastModifiedDate_format: Final[str] = '%Y-%m-%d %H:%M:%S'


# @dataclass
class TableExample(BaseTable):
    row_type = RowExample


if __name__ == '__main__':
    print('test_table_printer START', '='*50)

    if 0:  # RowExample Test - class method
        print('RowExample Test - class method')
        print(RowExample.get_col_attr_names())
        print(RowExample.get_col_header_map())
        print(RowExample.get_col_header_len_map())

    if 0:  # RowExample Test - instance
        print('RowExample Test - instance')
        test_row = RowExample(ColInt=11, ColStr='some text')
        print(test_row.get_col_header_map())
        print(test_row.get_col_value_disp_len())

    if 0:  # calculate display length for wide and narrow characters
        print('get_display_length Test - wide narrow character display width')
        msg = 'aF'
        print(msg, get_display_length(msg))
        msg = '中'
        print(msg, get_display_length(msg))
        msg = '中a'
        print(msg, get_display_length(msg))
        msg = str(1)
        print(msg, get_display_length(msg))

    if 1:
        print('TableExample Test')
        table = TableExample()
        # # table.insert_row(RowExample())
        table.insert_row(RowExample(ColInt=1, ColStr='text', ColStrCn='短中文'))
        table.insert_row(RowExample(ColInt=2, ColStr='long text', ColStrCn='长中文'))
        table.insert_row(RowExample(ColInt=3, ColStr='some super long EnText', ColStrCn='短中文'))
        table.insert_row(RowExample(ColInt=4, ColStr='和最长英文一样长的中文', ColStrCn='很长很长特别长的中文'))
        table.insert_row(RowExample(ColInt=111, ColStr='带中文 text'))
        # table.insert_row(RowExample(ColInt=2, ColStr='some Text', __ColInt='new name'))
        table.print_table()
