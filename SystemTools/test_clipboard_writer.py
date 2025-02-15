import sys
from clipboard_writer import copy_to_clipboard


if __name__ == '__main__':
    # 使用示例
    text = f"Hello from {sys.platform}"
    print(text)
    copy_to_clipboard(text)
    print("内容已复制到剪贴板，可以尝试粘贴")
