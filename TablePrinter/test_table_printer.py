import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

from table_printer import BaseRow, BaseTable, ColumnAlignment, ColumnConfig, get_display_length
from table_printer_consts import BoxDrawingChar


@dataclass
class RowExample(BaseRow):
    """
    1. Every field is a column in the row. When define, a default value is required
    2. __<ColumnName>_config: if defined
        a. output will use the config.alias as title instead of <ColumnName> if not None.
        b. output will not display the column if config.hide is True.
        c. output will use config.format to format the string if <ColumnName> type is datetime.
    """
    ColInt: int = -1

    ColStr: str = 'N/A'
    __ColStr_config: Final[ColumnConfig] = ColumnConfig(alias='EN column alias', align=ColumnAlignment.LEFT, hide=False)

    ColStrCn: str = 'N/A'
    __ColStrCn_config: Final[ColumnConfig] = ColumnConfig(alias='中文别名', hide=True)

    ColHidden: str = 'N/A'
    __ColHidden_config: Final[ColumnConfig] = ColumnConfig(alias='不应该能看到这列', hide=True)

    LastModifiedDate: datetime = field(default_factory=datetime.now)  # test datetime column display
    __LastModifiedDate_config: Final[ColumnConfig] = ColumnConfig(
        alias='最后修改日期', hide=False, format='%Y-%m-%d %H:%M:%S'
    )


# @dataclass
class TableExample(BaseTable):
    row_type = RowExample


@dataclass
class RowEmployeeExample(BaseRow):
    Name: str = ''
    __Name_config: Final[ColumnConfig] = ColumnConfig(alias='名字')
    Age: int = None
    __Age_config: Final[ColumnConfig] = ColumnConfig(alias='年龄')
    Salary: int = None
    __Salary_config: Final[ColumnConfig] = ColumnConfig(alias='工资')
    InsertDt: datetime = field(default_factory=datetime.now)
    __InsertDt_config: Final[ColumnConfig] = ColumnConfig(hide=False, format='%H:%M:%S.%f')


class TableEmployeeExample(BaseTable):
    row_type = RowEmployeeExample


def test_table_with_order():
    print(test_table_with_order.__name__, '=' * 50)
    table = TableEmployeeExample()
    table.insert_row(RowEmployeeExample(Name='Rylee Mcdaniel', Age=21, Salary=5000))
    time.sleep(0.1)
    table.insert_row(RowEmployeeExample(Name='Miley Ritter', Age=25, Salary=6000))
    time.sleep(0.1)
    table.insert_row(RowEmployeeExample(Name='Zachery Wang', Age=27, Salary=7000))
    time.sleep(0.1)
    table.insert_row(RowEmployeeExample(Name='Carina Holland', Age=22, Salary=5000))
    time.sleep(0.1)
    table.insert_row(RowEmployeeExample(Name='Amya Thomas', Age=41, Salary=4000))
    time.sleep(0.1)
    table.insert_row(RowEmployeeExample(Name='Sadie Hinton', Age=32, Salary=4500))
    time.sleep(0.1)
    table.insert_row(RowEmployeeExample(Name='Santos George', Age=35, Salary=5500))
    time.sleep(0.1)
    table.insert_row(RowEmployeeExample(Name='Nikolai Valenzue', Age=45, Salary=4900))
    time.sleep(0.1)
    table.insert_row(RowEmployeeExample(Name='Mckenna Galloway', Age=33, Salary=5000))
    # table.print_table(order_by=['name', 'age', 'Salary'])  # test wrong order_by attribute
    table.print_table(order_by=['Name'])  # test sort 1 str column
    table.print_table(order_by=['Salary'])  # test sort 1 int columns
    table.print_table(order_by=['Salary', 'Name'])  # test sort multiple columns
    table.print_table(order_by=['Salary', 'Name'], ascending=[True, False])  # test sort multiple columns
    table.print_table(order_by=['InsertDt'])  # test sort on hidden column
    # table.print_table(group_by=['Salary'], order_by=['Salary'])


def test_table_with_customized_row_separator():
    print('test print table with customized row separator')

    @dataclass
    class RowOfficeExample(BaseRow):
        BuildingId: int = -1
        BuildingName: str = 'NA'
        DepartmentId: int = -1
        DepartmentName: str = 'NA'
        Floor: int = -1
        OfficeId: str = 'NA'

    class TableOfficeExample(BaseTable):
        row_type = RowOfficeExample

    # create table instance
    table = TableOfficeExample()
    offices = [
        RowOfficeExample(BuildingId=1, BuildingName='B1', DepartmentId=1, DepartmentName='D1', Floor=1, OfficeId=1),
        RowOfficeExample(BuildingId=1, BuildingName='B1', DepartmentId=1, DepartmentName='D1', Floor=1, OfficeId=2),
        RowOfficeExample(BuildingId=1, BuildingName='B1', DepartmentId=2, DepartmentName='D2', Floor=2, OfficeId=3),
        RowOfficeExample(BuildingId=1, BuildingName='B1', DepartmentId=2, DepartmentName='D2', Floor=2, OfficeId=4),
        RowOfficeExample(BuildingId=1, BuildingName='B1', DepartmentId=3, DepartmentName='D3', Floor=3, OfficeId=5),
        RowOfficeExample(BuildingId=2, BuildingName='B2', DepartmentId=3, DepartmentName='D3', Floor=1, OfficeId=6),
        RowOfficeExample(BuildingId=2, BuildingName='B2', DepartmentId=4, DepartmentName='D4', Floor=1, OfficeId=7),
        RowOfficeExample(BuildingId=2, BuildingName='B2', DepartmentId=4, DepartmentName='D4', Floor=2, OfficeId=8),
        RowOfficeExample(BuildingId=2, BuildingName='B2', DepartmentId=4, DepartmentName='D4', Floor=2, OfficeId=9),
    ]
    for office_row in offices:
        table.insert_row(office_row)

    # prepare output: get header line and header separator line
    lines = [table.get_table_header_str(), table.get_table_header_sep_str()]

    # prepare output: sort the rows and add customized separator for printing the table
    rows_sorted = table.get_sorted_rows(order_by=['BuildingId', 'Floor'], ascending=[True, False])

    # prepare output: insert row line and row separator line
    row_prev: RowOfficeExample = None
    for row in rows_sorted:
        # If you don't know what you are doing, it's recommended add the separator regarding to the sorting order.
        # Otherwise, you may see same column value being separated into different chunks and the output looks weird.
        row: RowOfficeExample
        if row_prev is not None and row_prev.BuildingId != row.BuildingId:
            lines.append(table.get_table_line_sep_str(
                sep_h=BoxDrawingChar.LIGHT_HORIZONTAL, sep_v=BoxDrawingChar.LIGHT_VERTICAL_AND_HORIZONTAL
            ))
        elif row_prev is not None and row_prev.Floor != row.Floor:
            lines.append(table.get_table_line_sep_str(
                sep_h=BoxDrawingChar.LIGHT_HORIZONTAL, sep_v=BoxDrawingChar.LIGHT_VERTICAL, dense=False
            ))
        lines.append(table.get_table_line_str(row))
        row_prev = row

    # print output
    for line in lines:
        print(line)


if __name__ == '__main__':
    print('test_table_printer START', '=' * 50)

    if 1:  # RowExample Test - class method
        print('RowExample Test - class method')
        print(RowExample.get_col_attr_names())
        print(RowExample.get_col_header_map())
        print(RowExample.get_col_header_len_map())

    if 1:  # RowExample Test - instance
        print('RowExample Test - instance')
        test_row = RowExample(ColInt=11, ColStr='some text')
        print(test_row.get_col_header_map())
        print(test_row.get_col_value_disp_len())

    if 1:  # calculate display length for wide and narrow characters
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
        table.insert_row(RowExample(ColInt=1, ColStr='text1', ColStrCn='短中文2'))
        table.insert_row(RowExample(ColInt=2, ColStr='long text', ColStrCn='长中文'))
        table.insert_row(RowExample(ColInt=3, ColStr='some super long EnText', ColStrCn='短中文'))
        table.insert_row(RowExample(ColInt=4, ColStr='和最长英文一样长的中文', ColStrCn='很长很长特别长的中文'))
        table.insert_row(RowExample(ColInt=111, ColStr='带中文 text'))
        table.insert_row(RowExample(ColInt=5))
        table.insert_row(RowExample(ColInt=1, ColStr='text2', ColStrCn='短中文1'))
        # table.insert_row(RowExample(ColInt=2, ColStr='some Text', __ColInt='new name'))  # test private var error
        table.print_table()

    test_table_with_order()
    test_table_with_customized_row_separator()
