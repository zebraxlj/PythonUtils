import sys

# 根据系统设置需要的变量
if sys.platform == 'win32':
    # Windows 系统（使用 ctypes）
    import ctypes
    from ctypes import wintypes

    # 定义 Windows API 函数和常量
    CF_UNICODETEXT = 13

    user32 = ctypes.WinDLL('user32')
    kernel32 = ctypes.WinDLL('kernel32')

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.lstrcpyW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    kernel32.lstrcpyW.restype = wintypes.LPWSTR
elif sys.platform == 'linux':
    pass
elif sys.platform == 'darwin':
    import subprocess
else:
    raise RuntimeError("Unsupported platform")


def copy_to_clipboard(text: str):
    if sys.platform == 'win32':
        copy_to_clipboard_windows(text)
    elif sys.platform == 'linux':
        try:
            copy_to_clipboard_linux(text)
            raise NotImplementedError('Linux 环境还没调通')
        except Exception as e:
            print('Linux 环境还没调通', e, sep='\n')
    elif sys.platform == 'darwin':
        try:
            # macOS 方案（使用 pbcopy 命令）
            subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
            raise NotImplementedError('macOS 的还没测过')
        except Exception as e:
            print('macOS 的还没测过', e, sep='\n')
    else:
        raise RuntimeError("Unsupported platform")


def copy_to_clipboard_linux(text: str):
    # 尝试常见剪贴板路径（非通用）
    paths = [
        '/proc/self/fd/1',  # 某些特殊场景
        '/dev/clipboard',
    ]
    for path in paths:
        try:
            with open(path, 'w') as f:
                f.write(text)
            return
        except Exception as e:
            print(path, e, sep='\n')
            continue
    raise RuntimeError("无可用剪贴板设备")


def copy_to_clipboard_windows(text: str):
    # 转换为 Windows 需要的 UTF-16 格式（带双空终止符）
    text += '\0'  # 确保文本有终止符
    utf16_text = text.encode('utf-16le')

    # 分配全局内存
    GMEM_MOVEABLE = 0x0002
    hglobal = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(utf16_text) + 2)

    # 锁定内存并拷贝数据
    ptr = kernel32.GlobalLock(hglobal)
    ctypes.memmove(
        ptr,
        utf16_text,
        len(utf16_text)
    )
    kernel32.GlobalUnlock(hglobal)

    # 设置剪贴板数据
    if user32.OpenClipboard(None):
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_UNICODETEXT, hglobal)
        user32.CloseClipboard()
    else:
        kernel32.GlobalFree(hglobal)
        raise RuntimeError("无法打开剪贴板")
