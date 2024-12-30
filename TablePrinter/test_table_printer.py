from dataclasses import dataclass
from typing import Final

from table_printer import BaseRow, BaseTable


@dataclass
class RowExample(BaseRow):
    """
    1. Every field is a column in the row. When define, a default value is required
    2. __<ColumnName>_alias: if defined, it will be used as the alias of the column in the output; otherwise, <ColumnName> will be used
    """
    ColInt: int = -1
    __ColInt_alias: Final[str] = 'integer column'
    __ColInt_hide: Final[bool] = True
    ColStr: str = 'N/A'
    __ColStr_alias: Final[str] = 'string column'


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

    if 1:
        print('TableExample Test')
        table = TableExample()
        # # table.insert_row(RowExample())
        table.insert_row(RowExample(ColInt=1, ColStr='text'))
        table.insert_row(RowExample(ColInt=2, ColStr='long text'))
        table.insert_row(RowExample(ColInt=3, ColStr='some super long text'))
        table.insert_row(RowExample(ColInt=111, ColStr='new line'))
        # table.insert_row(RowExample(ColInt=2, ColStr='some Text', __ColInt='new name'))
        print(table.print_table())
