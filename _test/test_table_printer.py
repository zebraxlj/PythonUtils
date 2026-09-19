import logging
import sys
import time
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import ClassVar, Optional
from unittest.mock import patch

PROJ_PATH = str(Path(__file__).resolve().parent.parent)
if PROJ_PATH not in sys.path:
    sys.path.insert(0, PROJ_PATH)

from TablePrinter.table_printer import (  # noqa: E402
    BaseRow, BaseTable,
    ColumnAlignment, ColumnConfig, CondFmtContain, CondFmtExactMatch, FontFormat, get_display_ansi_width
)
import TablePrinter.table_printer as table_printer  # noqa: E402
from ColorHelper.color_xterm_256 import ColorXTerm256  # noqa: E402
from TablePrinter.table_printer_consts import BoxDrawingChar  # noqa: E402


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
    __ColStr_config: ClassVar[ColumnConfig] = ColumnConfig(
        alias='EN column alias', align=ColumnAlignment.LEFT, hide=False
    )

    ColStrCn: str = 'N/A'
    __ColStrCn_config: ClassVar[ColumnConfig] = ColumnConfig(alias='中文别名', hide=True)

    ColHidden: str = 'N/A'
    __ColHidden_config: ClassVar[ColumnConfig] = ColumnConfig(alias='不应该能看到这列', hide=True)

    LastModifiedDate: datetime = field(default_factory=datetime.now)  # test datetime column display
    __LastModifiedDate_config: ClassVar[ColumnConfig] = ColumnConfig(
        alias='最后修改日期', hide=False, format='%Y-%m-%d %H:%M:%S'
    )


# @dataclass
class TableExample(BaseTable):
    row_type = RowExample


@dataclass
class RowEmployeeExample(BaseRow):
    Name: str = ''
    __Name_config: ClassVar[ColumnConfig] = ColumnConfig(alias='名字')
    Age: int = None
    __Age_config: ClassVar[ColumnConfig] = ColumnConfig(alias='年龄')
    Salary: int = None
    __Salary_config: ClassVar[ColumnConfig] = ColumnConfig(alias='工资')
    InsertDt: datetime = field(default_factory=datetime.now)
    __InsertDt_config: ClassVar[ColumnConfig] = ColumnConfig(hide=False, format='%H:%M:%S.%f')


class TableEmployeeExample(BaseTable):
    row_type = RowEmployeeExample


def test_alternating_row_backgrounds():
    print(test_alternating_row_backgrounds.__name__, '=' * 50)
    """Print row backgrounds and verify they do not override match highlighting."""
    @dataclass
    class Row(BaseRow):
        Value: str = ''
        Marker: str = ''
        __Value_config: ClassVar[ColumnConfig] = ColumnConfig(
            conditional_format=CondFmtExactMatch(match_target='alert')
        )

    class Table(BaseTable):
        row_type = Row
        ENABLE_ROW_BACKGROUND = True
        ROW_BACKGROUND_COLORS = (ColorXTerm256.COLOR_120, ColorXTerm256.COLOR_231)
        HEADER_BACKGROUND_COLOR = ColorXTerm256.COLOR_35
        HEADER_FOREGROUND_COLOR = ColorXTerm256.COLOR_231
        HEADER_BOLD = True
        ENABLE_HEADER_SEPARATOR = False

    table = Table()
    table.insert_row(Row(Value='normal1', Marker='1'))
    table.insert_row(Row(Value='normal2', Marker='2'))
    table.insert_row(Row(Value='alert', Marker='3'))
    table.insert_row(Row(Value='normal3', Marker='4'))

    output = StringIO()
    with redirect_stdout(output):
        table.print_table()
    print(output.getvalue(), end='')


def test_default_column_config_has_no_mutable_conditional_format():
    assert ColumnConfig().conditional_format is None


def test_href_replaces_only_the_cell_content(monkeypatch):
    monkeypatch.setattr(table_printer, 'can_display_href', lambda: True)

    @dataclass
    class Row(BaseRow):
        Value: str = ' '
        Value_href: str = 'https://example.test'

    class Table(BaseTable):
        row_type = Row

    table = Table()
    table.insert_row(Row())
    rendered = table.get_table_line_str(table.row_list[0])

    assert rendered.count('\x1b]8;;https://example.test\x1b\\') == 1


def test_overline_survives_cell_formatting():
    print(test_overline_survives_cell_formatting.__name__, '=' * 50)

    @dataclass
    class Row(BaseRow):
        Value: str = ''
        Marker: str = ''
        __Value_config: ClassVar[ColumnConfig] = ColumnConfig(
            conditional_format=CondFmtExactMatch(match_target='alert')
        )

    class Table(BaseTable):
        row_type = Row

    table = Table()
    rows = [
        Row(Value='normal', Marker='before'),
        Row(Value='normal', Marker='overlined'),
        Row(Value='alert', Marker='overlined'),
        Row(Value='normal', Marker='after'),
    ]
    for row in rows:
        table.insert_row(row)

    with patch.object(table_printer, 'can_display_ansi_color', return_value=True):
        rendered = [
            table.get_table_line_str(rows[1], row_index=1, overline=True),
            table.get_table_line_str(rows[2], row_index=1, overline=True),
        ]
        print(table.CHAR_LN.join((
            table.get_table_header_str(),
            table.get_table_header_sep_str(),
            table.get_table_line_str(rows[0], row_index=0),
            *rendered,
            table.get_table_line_str(rows[2], row_index=2),
        )))


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

    def add_group_separator(
            row_prev: Optional[RowOfficeExample], row: RowOfficeExample, display_line_index: int
            ) -> Optional[str]:
        """Insert a separator while TablePrinter owns the display-line index."""
        if row_prev is not None and row_prev.BuildingId != row.BuildingId:
            return table.get_table_line_sep_str(
                sep_h=BoxDrawingChar.LIGHT_HORIZONTAL,
                sep_v=BoxDrawingChar.LIGHT_VERTICAL_AND_HORIZONTAL,
                row_index=display_line_index,
            )
        if row_prev is not None and row_prev.Floor != row.Floor:
            return table.get_table_line_sep_str(
                sep_h=BoxDrawingChar.LIGHT_HORIZONTAL,
                sep_v=BoxDrawingChar.LIGHT_VERTICAL,
                dense=False,
                row_index=display_line_index,
            )
        return None

    # The hook may also return multiple lines, replace a row, or return None to skip it.
    print(table.to_table_str(
        order_by=['BuildingId', 'Floor'],
        ascending=[True, False],
        before_row=add_group_separator,
    ))


def test_table_with_conditional_formatting():
    print('test print table with conditional formatting')

    @dataclass
    class RowConditionalFormatExample(BaseRow):
        RowId: int = None
        FmtContainStr: str = 'NA'
        __FmtContainStr_config = ColumnConfig(conditional_format=CondFmtContain(contain_target='abc'))
        FmtExactMatchStr: str = 'NA'
        __FmtExactMatchStr_config = ColumnConfig(conditional_format=CondFmtExactMatch(match_target='ok'))
        FmtExactMatchBool: str = 'NA'
        __FmtExactMatchBool_config = ColumnConfig(conditional_format=CondFmtExactMatch(match_target=True))
        FmtExactMatchInt: str = 'NA'
        __FmtExactMatchInt_config = ColumnConfig(conditional_format=CondFmtExactMatch(match_target=-1))

    class TableConditionalFormatExample(BaseTable):
        row_type = RowConditionalFormatExample

    table = TableConditionalFormatExample()
    rows = [
        RowConditionalFormatExample(
            RowId=1, FmtContainStr='Say hello', FmtExactMatchStr='ok', FmtExactMatchBool=False, FmtExactMatchInt=-1
        ),
        RowConditionalFormatExample(
            RowId=2, FmtContainStr='Say abc', FmtExactMatchStr='fail', FmtExactMatchBool=True, FmtExactMatchInt=1
        ),
    ]
    for row in rows:
        table.insert_row(row)
    table.print_table()


def test_configure_logger():
    """演示调用方为 TablePrinter 显式配置日志。"""
    print('test configure logger handler', '=' * 50)

    # 库不配置 handler 或日志级别；调用方按自身格式和输出目标显式配置。
    tp_logger = logging.getLogger('TablePrinter.table_printer')
    custom_handler = logging.StreamHandler()
    custom_handler.setFormatter(logging.Formatter(
        '[%(levelname)s] %(funcName)s - %(message)s'
    ))

    # 保存并完整还原先前配置，避免测试影响其他调用方。
    original_level = tp_logger.level
    original_propagate = tp_logger.propagate
    try:
        tp_logger.setLevel(logging.DEBUG)
        tp_logger.propagate = False  # 防止也由 root logger 再输出一次
        tp_logger.addHandler(custom_handler)

        table = TableExample()
        table.insert_row(RowExample(ColInt=1, ColStr='logger test'))
        table.print_table()
    finally:
        tp_logger.removeHandler(custom_handler)
        tp_logger.setLevel(original_level)
        tp_logger.propagate = original_propagate


def test_table_with_href():
    print('test print table with url')

    @dataclass
    class RowHRefExample(BaseRow):
        WebsiteName: str = 'NA'
        WebsiteName_href: str = ''

    class TableHRefExample(BaseTable):
        row_type = RowHRefExample

    table_href = TableHRefExample()
    rows = [
        RowHRefExample(WebsiteName='Baidu href', WebsiteName_href='https://www.baidu.com'),
        RowHRefExample(WebsiteName='Bing href', WebsiteName_href='https://www.bing.com'),
    ]
    for row in rows:
        table_href.insert_row(row)
    table_href.print_table()

    @dataclass
    class RowUrlExample(BaseRow):
        WebsiteName: str = 'NA'
        WebsiteName_url: str = ''

    class TableUrlExample(BaseTable):
        row_type = RowUrlExample

    table_url = TableUrlExample()
    rows = [
        RowUrlExample(WebsiteName='Baidu url', WebsiteName_url='https://www.baidu.com'),
        RowUrlExample(WebsiteName='Bing url', WebsiteName_url='https://www.bing.com'),
        RowUrlExample(WebsiteName='Blank url'),
    ]
    for row in rows:
        table_url.insert_row(row)
    table_url.print_table()


def test_table_printer():
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
        print('get_display_ansi_width Test - wide narrow character display width')
        msg = 'aF'
        print(msg, get_display_ansi_width(msg))
        msg = '中'
        print(msg, get_display_ansi_width(msg))
        msg = '中a'
        print(msg, get_display_ansi_width(msg))
        msg = str(1)
        print(msg, get_display_ansi_width(msg))

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
    test_overline_survives_cell_formatting()
    test_alternating_row_backgrounds()
    test_table_with_customized_row_separator()
    test_table_with_conditional_formatting()
    test_table_with_href()
    test_configure_logger()


if __name__ == '__main__':
    test_table_printer()
