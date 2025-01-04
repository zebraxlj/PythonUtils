from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

from table_printer import BaseRow, BaseTable, get_display_length


@dataclass
class RowExample(BaseRow):
    """
    1. Every field is a column in the row. When define, a default value is required
    2. __<ColumnName>_alias: if defined, output title will show alias instead of <ColumnName>.
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


@dataclass
class RowEmployeeExample(BaseRow):
    Name: str = ''
    __Name_alias: Final[str] = '名字'
    Age: int = None
    __Age_alias: Final[str] = '年龄'
    Salary: int = None
    __Salary_alias: Final[str] = '工资'


class TableEmployeeExample(BaseTable):
    row_type = RowEmployeeExample


def test_table_with_order():
    print(test_table_with_order.__name__, '=' * 50)
    table = TableEmployeeExample()
    table.insert_row(RowEmployeeExample(Name='Rylee Mcdaniel', Age=21, Salary=5000))
    table.insert_row(RowEmployeeExample(Name='Miley Ritter', Age=25, Salary=6000))
    table.insert_row(RowEmployeeExample(Name='Zachery Wang', Age=27, Salary=7000))
    table.insert_row(RowEmployeeExample(Name='Carina Holland', Age=22, Salary=5000))
    table.insert_row(RowEmployeeExample(Name='Amya Thomas', Age=41, Salary=4000))
    table.insert_row(RowEmployeeExample(Name='Sadie Hinton', Age=32, Salary=4500))
    table.insert_row(RowEmployeeExample(Name='Santos George', Age=35, Salary=5500))
    table.insert_row(RowEmployeeExample(Name='Nikolai Valenzue', Age=45, Salary=4900))
    table.insert_row(RowEmployeeExample(Name='Mckenna Galloway', Age=33, Salary=5000))
    # table.print_table(order_by=['name', 'age', 'Salary'])  # test wrong order_by attribute
    table.print_table(order_by=['Name'])  # test sort 1 str column
    table.print_table(order_by=['Salary'])  # test sort 1 int columns
    table.print_table(order_by=['Salary', 'Name'])  # test sort multiple columns
    table.print_table(order_by=['Salary', 'Name'], ascending=[True, False])  # test sort multiple columns


if __name__ == '__main__':
    print('test_table_printer START', '=' * 50)

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

    if 0:
        print('TableExample Test')
        table = TableExample()
        # # table.insert_row(RowExample())
        table.insert_row(RowExample(ColInt=1, ColStr='text1', ColStrCn='短中文2'))
        table.insert_row(RowExample(ColInt=2, ColStr='long text', ColStrCn='长中文'))
        table.insert_row(RowExample(ColInt=3, ColStr='some super long EnText', ColStrCn='短中文'))
        table.insert_row(RowExample(ColInt=4, ColStr='和最长英文一样长的中文', ColStrCn='很长很长特别长的中文'))
        table.insert_row(RowExample(ColInt=111, ColStr='带中文 text'))
        table.insert_row(RowExample(ColInt=5))
        table.insert_row(RowExample(ColInt=1, ColStr='text2', ColStrCn='短中文1'))
        # table.insert_row(RowExample(ColInt=2, ColStr='some Text', __ColInt='new name'))  # test private var error
        # table.print_table()

    test_table_with_order()
