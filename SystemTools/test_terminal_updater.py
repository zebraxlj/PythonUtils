import time
import sys

from terminal_updater import TerminalUpdater


def test_ansi_escape_char():
    # 打印初始内容
    sys.stdout.write("Original Line 1\n")
    sys.stdout.write("Original Line 2\n")
    sys.stdout.flush()

    time.sleep(2)  # 等待一段时间，模拟用户看到初始内容

    # 修改第一行
    sys.stdout.write("\033[2A")  # 向上移动两行到第一行
    sys.stdout.write("\r")       # 回到行首
    sys.stdout.write("\033[2K")  # 清除整行内容
    sys.stdout.write("Modified Line 1\n")  # 覆盖第一行
    sys.stdout.flush()

    time.sleep(2)  # 等待一段时间，模拟用户看到初始内容

    # 修改第二行
    # sys.stdout.write("\033[1A")  # 向上移动一行到第二行
    # sys.stdout.write("\r")       # 回到行首
    sys.stdout.write("\033[2K")  # 清除整行内容
    sys.stdout.write("Modified Line 2\n")  # 覆盖第二行
    sys.stdout.flush()

    time.sleep(2)  # 等待一段时间，展示修改后的效果
    sys.exit()     # 退出程序


def test_terminal_updater_simple():
    terminal = TerminalUpdater()

    lines = [
        'line 1',
        'line 2',
    ]
    terminal.update(lines)

    time.sleep(1)
    lines[0] = 'line 1 new'
    terminal.update(lines)

    time.sleep(1)
    lines[1] = 'line 2 new'
    terminal.update(lines)

    time.sleep(1)
    lines.append('line 3')
    terminal.update(lines)

    time.sleep(1)
    lines.append('line 4')
    terminal.update(lines)

    time.sleep(1)
    lines.pop(2)
    terminal.update(lines)

    time.sleep(1)
    lines.append('line 5')
    terminal.update(lines)


if __name__ == "__main__":
    # test_ansi_escape_char()
    test_terminal_updater_simple()
