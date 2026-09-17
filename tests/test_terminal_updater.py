import pytest

from SystemTools.terminal_updater import SingletonMeta, TerminalController, TerminalUpdater


@pytest.fixture(autouse=True)
def reset_singleton():
    """SingletonMeta keeps instances forever; reset between tests to isolate state."""
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()


@pytest.fixture
def term(capsys):
    return TerminalUpdater()


class TestCursorControl:
    def test_move_up(self, capsys):
        TerminalController.CursorMoveUp(3)
        assert capsys.readouterr().out == '\033[3A'

    def test_move_home(self, capsys):
        TerminalController.CursorMoveToHome()
        assert capsys.readouterr().out == '\033[H'

    def test_erase_entire_line(self, capsys):
        TerminalController.EraseEntireLine()
        assert capsys.readouterr().out == '\033[2K'


class TestTerminalUpdater:
    def test_first_update_prints_all_lines(self, term, capsys):
        term.update(['line 1', 'line 2'])
        assert capsys.readouterr().out == 'line 1\nline 2\n'

    def test_no_change_just_moves_cursor(self, term, capsys):
        term.update(['line 1', 'line 2'])
        capsys.readouterr()  # clear
        term.update(['line 1', 'line 2'])
        # move to previous line begin (2 lines up), then down-begin per unchanged line
        assert capsys.readouterr().out == '\033[2F\033[1E\033[1E'

    def test_change_redraws_line(self, term, capsys):
        term.update(['line 1', 'line 2'])
        capsys.readouterr()
        term.update(['line 1', 'changed'])
        out = capsys.readouterr().out
        assert out.startswith('\033[2F')  # back to first line
        assert '\033[1E' in out           # skip first unchanged line
        assert '\033[2K' in out           # erase then rewrite second line
        assert 'changed' in out

    def test_grow_lines(self, term, capsys):
        term.update(['a'])
        capsys.readouterr()
        term.update(['a', 'b'])
        out = capsys.readouterr().out
        assert '\033[2K' in out
        assert 'b' in out

    def test_shrink_lines_erases_carry_over(self, term, capsys):
        term.update(['a', 'b', 'c'])
        capsys.readouterr()
        term.update(['a'])
        out = capsys.readouterr().out
        assert '\033[2K' in out          # erase the two removed lines
        assert 'b' not in out and 'c' not in out

    def test_empty_update_erases_everything(self, term, capsys):
        term.update(['a', 'b'])
        capsys.readouterr()
        term.update([])
        assert 'a' not in capsys.readouterr().out

    def test_caller_mutating_same_list_still_redraws(self, term, capsys):
        """Regression: updating the same list object in place must redraw the change.

        Previously __prev_lines aliased the caller's list when nothing changed,
        so an in-place mutation between update() calls compared equal and the
        change was silently dropped.
        """
        lines = ['status: idle']
        term.update(lines)
        capsys.readouterr()
        lines[0] = 'status: done'  # in-place mutation of the same list object
        term.update(lines)
        out = capsys.readouterr().out
        assert 'status: done' in out
        assert 'status: idle' not in out

    def test_singleton_instance_reuse(self):
        assert TerminalUpdater() is TerminalUpdater()


class TestTerminalControllerDefaults:
    def test_cursor_request_position(self, capsys):
        TerminalController.CursorRequestPosition()
        assert capsys.readouterr().out == '\033[6n'

    def test_ansi_region_constants(self):
        # The class-level docstring comments are fine; just ensure no writing
        # to stdout at import time happened (module import already succeeded).
        assert hasattr(TerminalController, 'CursorMoveToHome')