import sys
from pathlib import Path

PROJ_PATH = str(Path(__file__).resolve().parent.parent)
if PROJ_PATH not in sys.path:
    sys.path.insert(0, PROJ_PATH)

from ColorHelper.color_xterm_256 import ColorXTerm256  # noqa: E402


def test_color_xterm_256():
    for row in range(8):
        color = ColorXTerm256(row)
        color_light = ColorXTerm256(row + 8)
        print(
            f"\033[48;5;{color}m{color.name:>8}{color:>2} \033[0m"
            f"\033[48;5;{color_light}m {color_light:<3}{color_light.name:<15}\033[0m"
            f"\033[38;5;{color}m{color.name:>8}{color:>2} \033[0m"
            f"\033[38;5;{color_light}m {color_light:<3}{color_light.name:<15}\033[0m"
        )
    print()

    for block in range(16, 22):
        for row in range(6):
            row_colors = []
            for col in range(6):
                row_colors.append(ColorXTerm256(block + row * 36 + col * 6))
            print(
                ''.join([f"\033[;48;5;{color}m{color:^5}\033[0m" for color in row_colors]),
                ''.join([f"\033[;38;5;{color}m{color:^5}\033[0m" for color in row_colors])
            )
    print()

    for block in range(16, 197, 36):
        for row in range(6):
            row_colors = []
            for col in range(6):
                row_colors.append(ColorXTerm256(block + row * 6 + col))
            print(
                ''.join([f"\033[;48;5;{color}m{color:^5}\033[0m" for color in row_colors]),
                ''.join([f"\033[;38;5;{color}m{color:^5}\033[0m" for color in row_colors])
            )

    print()

    for block in range(16, 197, 36):
        for row in range(6):
            row_colors = []
            for col in range(6):
                row_colors.append(ColorXTerm256(block + row + col * 6))
            print(
                ''.join([f"\033[;48;5;{color}m{color:^5}\033[0m" for color in row_colors]),
                ''.join([f"\033[;38;5;{color}m{color:^5}\033[0m" for color in row_colors])
            )

    print()

    for row in range(1, 4):
        row_colors = [ColorXTerm256(231 + row * col) for col in range(1, 9)]
        print(
            ''.join([f"\033[;48;5;{color}m{color:^5}\033[0m" for color in row_colors]),
            ''.join([f"\033[;38;5;{color}m{color:^5}\033[0m" for color in row_colors])
        )


if __name__ == '__main__':
    test_color_xterm_256()
