import logging
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from datetime import datetime
from io import StringIO
from typing import ClassVar

import pytest

from ColorHelper.color_xterm_256 import ColorXTerm256
from TablePrinter.table_printer import (
    COND_FMT_DEFAULT, BaseRow, BaseTable, ColumnAlignment, ColumnConfig,
    CondFmtContain, CondFmtExactMatch, FontFormat, can_display_ansi_color,
    can_display_href, get_display_ansi_width,
)
import TablePrinter.table_printer as table_printer


@dataclass
class RowExample(BaseRow):
    ColInt: int = -1
    ColStr: str = 'N/A'
    __ColStr_config: ClassVar[ColumnConfig] = ColumnConfig(
        alias='EN column alias', align=ColumnAlignment.LEFT, hide=False
    )
    ColStrCn: str = 'N/A'
    __ColStrCn_config: ClassVar[ColumnConfig] = ColumnConfig(alias='中文别名', hide=True)
    LastModifiedDate: datetime = field(default_factory=datetime.now)
    __LastModifiedDate_config: ClassVar[ColumnConfig] = ColumnConfig(
        alias='最后修改日期', hide=False, format='%Y-%m-%d %H:%M:%S'
    )


class TableExample(BaseTable):
    row_type = RowExample


@pytest.fixture(autouse=True)
def reset_ansi_cache():
    """can_display_ansi_color caches its result process-wide; reset per test."""
    table_printer._ansi_color_supported = None
    yield
    table_printer._ansi_color_supported = None


class TestDisplayWidth:
    def test_ascii(self):
        assert get_display_ansi_width('abc') == 3

    def test_wide_char(self):
        assert get_display_ansi_width('中') == 2

    def test_mixed(self):
        assert get_display_ansi_width('中a') == 3

    def test_empty(self):
        assert get_display_ansi_width('') == 0

    def test_emoji(self):
        assert get_display_ansi_width('🔥') == 2


class TestColumnDiscovery:
    def test_hidden_column_excluded(self):
        assert 'ColStrCn' not in RowExample.get_col_attr_names()
        assert 'ColStr' in RowExample.get_col_attr_names()

    def test_config_attrs_not_columns(self):
        assert all(not name.endswith('_config') for name in RowExample.get_col_attr_names())

    def test_header_alias_map(self):
        header_map = RowExample.get_col_header_map()
        assert header_map['ColStr'] == 'EN column alias'

    def test_get_config_returns_alias(self):
        assert RowExample.get_config('ColStr').alias == 'EN column alias'

    def test_get_config_on_non_data_attr_raises(self):
        # the mangled config attribute name (_RowExample__ColStr_config) is not
        # a data column and must be rejected
        with pytest.raises(ValueError):
            RowExample.get_config('_RowExample__ColStr_config')

    def test_get_config_default_for_plain_attr(self):
        config = RowExample.get_config('ColInt')
        assert isinstance(config, ColumnConfig)
        assert config.alias is None


class TestRowValues:
    def test_col_value_disp_formats_datetime(self):
        row = RowExample(ColInt=1)
        disp = row.get_col_value_disp()
        assert 'LastModifiedDate' in disp
        # formatted per the '%Y-%m-%d %H:%M:%S' config
        datetime.strptime(disp['LastModifiedDate'], '%Y-%m-%d %H:%M:%S')

    def test_col_value_disp_len(self):
        row = RowExample(ColInt=1)
        assert row.get_col_value_disp_len()['ColInt'] == len(str(1))


class TestSorting:
    def _employee_table(self):
        @dataclass
        class RowEmployee(BaseRow):
            Name: str = ''
            Age: int = 0
            Salary: int = 0

        class TableEmployee(BaseTable):
            row_type = RowEmployee

        table = TableEmployee()
        table.insert_row(RowEmployee(Name='Amy', Age=30, Salary=5000))
        table.insert_row(RowEmployee(Name='Bob', Age=25, Salary=6000))
        table.insert_row(RowEmployee(Name='Cid', Age=35, Salary=5000))
        return table

    def test_sort_single_asc(self):
        table = self._employee_table()
        rows = table.get_sorted_rows(order_by=['Salary'])
        assert [r.Salary for r in rows] == [5000, 5000, 6000]

    def test_sort_single_desc(self):
        table = self._employee_table()
        rows = table.get_sorted_rows(order_by=['Salary'], ascending=[False])
        assert [r.Salary for r in rows] == [6000, 5000, 5000]

    def test_sort_multi_mixed(self):
        table = self._employee_table()
        rows = table.get_sorted_rows(order_by=['Salary', 'Name'], ascending=[True, False])
        # salary asc, then name desc: Cid (5000) before Amy (5000)
        assert [r.Name for r in rows] == ['Cid', 'Amy', 'Bob']

    def test_sort_unknown_attr_raises(self):
        table = self._employee_table()
        with pytest.raises(ValueError, match='Unknown attribute'):
            table.get_sorted_rows(order_by=['Bogus'])

    def test_sort_empty_order_by_raises(self):
        table = self._employee_table()
        with pytest.raises(ValueError):
            table.get_sorted_rows(order_by=[])

    def test_sort_ascending_length_mismatch_raises(self):
        table = self._employee_table()
        with pytest.raises(ValueError):
            table.get_sorted_rows(order_by=['Salary', 'Name'], ascending=[True])


class TestTableRendering:
    def test_header_and_separator(self):
        table = TableExample()
        header = table.get_table_header_str()
        assert 'EN column alias' in header
        assert 'ColInt' in header
        sep = table.get_table_header_sep_str()
        assert '═' in sep  # double horizontal

    def test_row_lines(self):
        table = TableExample()
        table.insert_row(RowExample(ColInt=7, ColStr='hello'))
        line = table.get_table_line_str(table.row_list[0])
        assert '│' in line  # LIGHT_VERTICAL column separator
        assert 'hello' in line

    def test_insert_wrong_type_raises(self):
        @dataclass
        class OtherRow(BaseRow):
            X: int = 0

        table = TableExample()
        with pytest.raises(TypeError):
            table.insert_row(OtherRow())

    def test_print_table_plain_output(self):
        """Redirected (piped) stdout must produce no ANSI escape sequences."""
        table = TableExample()
        table.insert_row(RowExample(ColInt=1, ColStr='x'))
        buf = StringIO()
        with redirect_stdout(buf):
            table.print_table()
        out = buf.getvalue()
        assert '\x1b[' not in out
        assert 'EN column alias' in out

    def test_widths_expand_with_content(self):
        table = TableExample()
        table.insert_row(RowExample(ColInt=1, ColStr='short'))
        assert table._get_col_max_disp_len()['ColStr'] == get_display_ansi_width('short')
        table.insert_row(RowExample(ColInt=2, ColStr='much longer text'))
        assert table._get_col_max_disp_len()['ColStr'] == get_display_ansi_width('much longer text')


class TestConditionalFormatting:
    def test_exact_match(self):
        fmt = CondFmtExactMatch(match_target='ok')
        assert fmt.is_condition_match('ok')
        assert not fmt.is_condition_match('not ok')

    def test_exact_match_str_coercion(self):
        fmt = CondFmtExactMatch(match_target=True)
        assert fmt.is_condition_match('True')

    def test_exact_match_raises_when_unset(self):
        fmt = CondFmtExactMatch()
        with pytest.raises(ValueError):
            fmt.is_condition_match('anything')

    def test_contain(self):
        fmt = CondFmtContain(contain_target='abc')
        assert fmt.is_condition_match('say abc now')
        assert not fmt.is_condition_match('say xyz')

    def test_contain_raises_when_unset(self):
        fmt = CondFmtContain()
        with pytest.raises(ValueError):
            fmt.is_condition_match('x')

    def test_apply_format_wraps(self):
        fmt = CondFmtExactMatch(match_target='x', format=FontFormat(BgColor=ColorXTerm256.RED))
        assert '\x1b[' in fmt.apply_format('x')

    def test_default_cond_fmt_is_shared_sentinel(self):
        assert COND_FMT_DEFAULT is not None

    def test_conditional_format_applied_to_column(self):
        @dataclass
        class RowCond(BaseRow):
            Val: str = ''
            __Val_config: ClassVar[ColumnConfig] = ColumnConfig(
                conditional_format=CondFmtExactMatch(match_target='alert')
            )

        class TableCond(BaseTable):
            row_type = RowCond
            HEADER_BACKGROUND_COLOR = None
            HEADER_FOREGROUND_COLOR = None

        table = TableCond()
        table.insert_row(RowCond(Val='alert'))
        # force color on to inspect formatting code path
        table_printer._ansi_color_supported = True
        line = table.get_table_line_str(table.row_list[0], row_index=0)
        assert '48;5;' in line  # background color emitted


class TestHref:
    def test_href_omitted_when_not_tty(self, monkeypatch):
        monkeypatch.setattr(table_printer, '_is_stdout_tty', lambda: False)
        assert can_display_href() is False

        @dataclass
        class RowHRef(BaseRow):
            Website: str = 'NA'
            Website_href: str = ''

        class TableHRef(BaseTable):
            row_type = RowHRef

        table = TableHRef()
        table.insert_row(RowHRef(Website='Baidu', Website_href='https://www.baidu.com'))
        line = table.get_table_line_str(table.row_list[0])
        assert '\x1b]8;;' not in line  # no OSC-8 escape in plain output
        assert 'Baidu' in line

    def test_href_emitted_when_tty(self, monkeypatch):
        monkeypatch.setattr(table_printer, '_is_stdout_tty', lambda: True)
        assert can_display_href() is True

        @dataclass
        class RowHRef(BaseRow):
            Website: str = 'NA'
            Website_href: str = ''

        class TableHRef(BaseTable):
            row_type = RowHRef

        table = TableHRef()
        table.insert_row(RowHRef(Website='Baidu', Website_href='https://www.baidu.com'))
        line = table.get_table_line_str(table.row_list[0])
        assert '\x1b]8;;https://www.baidu.com\x1b\\' in line


class TestColorDetection:
    def test_ansi_color_false_when_piped(self, monkeypatch):
        monkeypatch.setattr(table_printer, '_is_stdout_tty', lambda: False)
        assert can_display_ansi_color() is False

    def test_ansi_color_true_on_tty_posix(self, monkeypatch):
        monkeypatch.setattr(table_printer, '_is_stdout_tty', lambda: True)
        assert can_display_ansi_color() is True

    def test_color_gated_table_output(self, monkeypatch):
        """Row banding must not emit escapes on piped stdout."""
        monkeypatch.setattr(table_printer, '_is_stdout_tty', lambda: False)

        @dataclass
        class RowB(BaseRow):
            A: str = ''

        class TableB(BaseTable):
            row_type = RowB
            ENABLE_ROW_BACKGROUND = True
            ENABLE_COLOR = True

        table = TableB()
        table.insert_row(RowB(A='x'))
        line = table.get_table_line_str(table.row_list[0], row_index=0)
        assert '\x1b[' not in line


class TestRowBackground:
    def test_banding_alternates(self, monkeypatch):
        monkeypatch.setattr(table_printer, '_is_stdout_tty', lambda: True)

        @dataclass
        class RowB(BaseRow):
            A: str = ''

        class TableB(BaseTable):
            row_type = RowB
            ENABLE_ROW_BACKGROUND = True
            ROW_BACKGROUND_COLORS = (ColorXTerm256.COLOR_120, ColorXTerm256.COLOR_231)

        table = TableB()
        assert table._get_row_background_color(0, True) == ColorXTerm256.COLOR_120
        assert table._get_row_background_color(1, True) == ColorXTerm256.COLOR_231
        assert table._get_row_background_color(2, True) == ColorXTerm256.COLOR_120

    def test_banding_disabled(self):
        @dataclass
        class RowB(BaseRow):
            A: str = ''

        class TableB(BaseTable):
            row_type = RowB

        table = TableB()
        assert table._get_row_background_color(0, True) is None

    def test_banding_negative_index_raises(self):
        @dataclass
        class RowB(BaseRow):
            A: str = ''

        class TableB(BaseTable):
            row_type = RowB
            ENABLE_ROW_BACKGROUND = True

        table = TableB()
        with pytest.raises(ValueError):
            table._get_row_background_color(-1, True)

    def test_banding_needs_color(self, monkeypatch):
        monkeypatch.setattr(table_printer, '_is_stdout_tty', lambda: False)

        @dataclass
        class RowB(BaseRow):
            A: str = ''

        class TableB(BaseTable):
            row_type = RowB
            ENABLE_ROW_BACKGROUND = True

        table = TableB()
        assert table._get_row_background_color(0, can_display_ansi_color()) is None


class TestFontFormat:
    def test_plain_text_no_codes(self):
        fmt = FontFormat(BgColor=None, FgColor=None)
        assert fmt.apply_format('x') == 'x'

    def test_bold(self):
        fmt = FontFormat(BgColor=None, FgColor=None, Bold=True)
        assert fmt.apply_format('x') == '\x1b[1mx\x1b[0m'

    def test_colors(self):
        fmt = FontFormat(BgColor=ColorXTerm256.RED, FgColor=ColorXTerm256.WHITE)
        assert fmt.apply_format('x') == '\x1b[48;5;1;38;5;7mx\x1b[0m'


class TestLoggerConfig:
    def test_default_logger_has_stream_handler_that_apps_can_override(self):
        """The library installs a default StreamHandler; apps can remove it."""
        logger = logging.getLogger('TablePrinter.table_printer')
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_logger_level(self):
        logger = logging.getLogger('TablePrinter.table_printer')
        assert logger.level == logging.INFO


class TestEmptyCell:
    def test_empty_cell_render_does_not_corrupt_padding(self):
        """Regression: an empty string cell used to explode str.replace padding."""
        @dataclass
        class RowE(BaseRow):
            Name: str = ''
            Link: str = ''
            Link_href: str = ''

        class TableE(BaseTable):
            row_type = RowE

        table = TableE()
        table.insert_row(RowE(Name='x', Link='', Link_href='https://e.com'))
        line = table.get_table_line_str(table.row_list[0])
        # no href escape spam from an empty Link cell
        assert '\x1b]8;;' not in line
        assert '│' in line