import sys
from copy import deepcopy
from typing import List


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TerminalController:
    """ use ANSI escape sequence to control the behavior in terminal, such as move cursor up, clear line, etc. """
    # region Cursor Control
    '''
    ESC Code Sequence	Description
    \033[H	moves cursor to home position (0, 0)
    \033[{line};{column}H
    \033[{line};{column}f	moves cursor to line #, column #
    \033[#A	moves cursor up # lines
    \033[#B	moves cursor down # lines
    \033[#C	moves cursor right # columns
    \033[#D	moves cursor left # columns
    \033[#E	moves cursor to beginning of next line, # lines down
    \033[#F	moves cursor to beginning of previous line, # lines up
    \033[#G	moves cursor to column #
    \033[6n	request cursor position (reports as \033[#;#R)
    ESC M	moves cursor one line up, scrolling if needed
    '''
    @staticmethod
    def CursorMoveToHome() -> None:
        sys.stdout.write('\033[H')

    @staticmethod
    def CursorMoveUp(num: int) -> None:
        sys.stdout.write(f'\033[{num}A')

    @staticmethod
    def CursorMoveDown(num: int) -> None:
        sys.stdout.write(f'\033[{num}B')

    @staticmethod
    def CursorMoveRight(num: int) -> None:
        sys.stdout.write(f'\033[{num}C')

    @staticmethod
    def CursorMoveLeft(num: int) -> None:
        sys.stdout.write(f'\033[{num}D')

    @staticmethod
    def CursorMoveNextBegin(num: int) -> None:
        sys.stdout.write(f'\033[{num}E')

    @staticmethod
    def CursorMovePrevBegin(num: int) -> None:
        sys.stdout.write(f'\033[{num}F')

    @staticmethod
    def CursorMoveToColumn(num: int) -> None:
        sys.stdout.write(f'\033[{num}G')

    @staticmethod
    def CursorMoveOneLineUpWithScroll() -> None:
        sys.stdout.write('\033 M')

    @staticmethod
    def CursorRequestPosition():
        sys.stdout.write('\033[6n')
    # endregion Cursor Control

    # region Erase Function
    '''
    ESC Code Sequence	Description
    \033[J	erase in display (same as \033[0J)
    \033[0J	erase from cursor until end of screen
    \033[1J	erase from cursor to beginning of screen
    \033[2J	erase entire screen
    \033[3J	erase saved lines
    \033[K	erase in line (same as \033[0K)
    \033[0K	erase from cursor to end of line
    \033[1K	erase start of line to the cursor
    \033[2K	erase the entire line
    '''
    @staticmethod
    def EraseInDisplay() -> None:
        ''' same as EraseCursorToEndOfScreen '''
        sys.stdout.write('\033[J')

    @staticmethod
    def EraseCursorToEndOfScreen() -> None:
        sys.stdout.write('\033[0J')

    @staticmethod
    def EraseCursorToBeginOfScreen() -> None:
        sys.stdout.write('\033[1J')

    @staticmethod
    def EraseEntireScreen() -> None:
        sys.stdout.write('\033[2J')

    @staticmethod
    def EraseSavedLines() -> None:
        sys.stdout.write('\033[3J')

    @staticmethod
    def EraseInLine() -> None:
        ''' same as EraseFromCursorToEndOfLine '''
        sys.stdout.write('\033[K')

    @staticmethod
    def EraseFromCursorToEndOfLine() -> None:
        sys.stdout.write('\033[0K')

    @staticmethod
    def EraseFromCursorToStartOfLine() -> None:
        sys.stdout.write('\033[1K')

    @staticmethod
    def EraseEntireLine() -> None:
        sys.stdout.write('\033[2K')

    # endregion


class TerminalUpdater(metaclass=SingletonMeta):
    __prev_lines: List[str] = None
    # TODO：add lock to prevent racing condition in multi-threading run
    # TODO: use CursorRequestPosition to optimize the following cases:
    #       1. no cursor movement when there's no diff in a line; instead, move n lines when there's a diff in a line

    # 用于在输出 standard output 时，允许
    def update(self, lines: List[str]) -> None:
        # 将光标移至上次输出的开始位置，准备覆盖
        if self.__prev_lines:
            TerminalController.CursorMovePrevBegin(len(self.__prev_lines))

        # 若 第一次像 Terminal 输出 / 之前已清空输出，则 跳过每行检查直接输出
        if not self.__prev_lines:
            for line_text in lines:
                sys.stdout.write(f'{line_text}\n')
            sys.stdout.flush()
            self.__prev_lines = deepcopy(lines)
            return

        # 对每行进行检查，覆盖输出不同的行
        diff_cnt = 0
        for line_num, line_text in enumerate(lines):
            # 检查是否需要更新当前行
            is_diff = False
            if not self.__prev_lines or len(self.__prev_lines) <= line_num:
                # 第一次像 Terminal 输出，
                is_diff = True
                diff_cnt += 1
            elif line_text != self.__prev_lines[line_num]:
                is_diff = True
                diff_cnt += 1

            if is_diff:
                TerminalController.EraseEntireLine()
                sys.stdout.write(f'{line_text}\n')
            else:
                TerminalController.CursorMoveNextBegin(1)

        # 若 有行被删除，则 清楚后续的
        if len(lines) < len(self.__prev_lines):
            line_rm_cnt = len(self.__prev_lines) - len(lines)
            for _ in range(line_rm_cnt):
                TerminalController.EraseEntireLine()
                TerminalController.CursorMoveNextBegin(1)
            TerminalController.CursorMovePrevBegin(line_rm_cnt)

        sys.stdout.flush()
        self.__prev_lines = lines
        if diff_cnt > 0:
            self.__prev_lines = deepcopy(lines)
