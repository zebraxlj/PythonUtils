import shutil
import subprocess
import sys

# Platform-specific imports (only the ones needed by the current platform).
if sys.platform == 'win32':
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
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL
    kernel32.lstrcpyW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    kernel32.lstrcpyW.restype = wintypes.LPWSTR
elif sys.platform == 'darwin':
    pass
elif sys.platform != 'linux':
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def copy_to_clipboard(text: str) -> None:
    """Copy ``text`` to the system clipboard.

    Strategy, in order:
    1. Tkinter (works in interactive sessions with an X/Wayland display).
    2. System clipboard tool on the current platform (xclip/wl-copy on Linux,
       pbcopy on macOS, the Win32 API on Windows).

    Raises:
        RuntimeError: when no clipboard backend could copy the text.
    """
    try:
        _copy_via_tkinter(text)
        return
    except Exception as tk_err:
        print(f'tkinter clipboard write failed: {tk_err}')

    if sys.platform == 'win32':
        copy_to_clipboard_windows(text)
    elif sys.platform == 'linux':
        _copy_to_clipboard_linux(text)
    elif sys.platform == 'darwin':
        _copy_to_clipboard_darwin(text)


def _copy_via_tkinter(text: str) -> None:
    """Copy through Tk's clipboard. Requires a display; raises otherwise."""
    import tkinter as tk

    root = tk.Tk()
    try:
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()  # 增加事件循环处理，确保内容真正写入剪贴板
    finally:
        root.destroy()


def _run_tool(tool: str, *args: str, text: str) -> None:
    subprocess.run([tool, *args], input=text.encode('utf-8'), check=True)


def _copy_to_clipboard_linux(text: str) -> None:
    """Copy using wl-copy or xclip on Linux. Raises when neither is available."""
    tool = shutil.which('wl-copy') or shutil.which('xclip') or shutil.which('xsel')
    if tool is None:
        raise RuntimeError(
            'no clipboard tool found on Linux (install wl-clipboard, xclip, or xsel)'
        )
    if tool.endswith('xsel'):
        _run_tool(tool, '--clipboard', '--input', text=text)
    elif tool.endswith('xclip'):
        _run_tool(tool, '-selection', 'clipboard', text=text)
    else:
        _run_tool(tool, text=text)


def _copy_to_clipboard_darwin(text: str) -> None:
    """Copy using pbcopy on macOS."""
    tool = shutil.which('pbcopy')
    if tool is None:
        raise RuntimeError('pbcopy not found on macOS')
    _run_tool(tool, text=text)


def copy_to_clipboard_windows(text: str) -> None:
    """Copy via the Win32 clipboard API (fallback when tkinter is unavailable)."""
    # 转换为 Windows 需要的 UTF-16 格式（带双空终止符）
    text += '\0'  # 确保文本有终止符
    utf16_text = text.encode('utf-16le')

    # 分配全局内存
    GMEM_MOVEABLE = 0x0002
    hglobal = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(utf16_text) + 2)
    if not hglobal:
        raise RuntimeError('GlobalAlloc failed')

    try:
        # 锁定内存并拷贝数据
        ptr = kernel32.GlobalLock(hglobal)
        if not ptr:
            raise RuntimeError('GlobalLock failed')
        ctypes.memmove(ptr, utf16_text, len(utf16_text))
        kernel32.GlobalUnlock(hglobal)

        # 设置剪贴板数据
        if not user32.OpenClipboard(None):
            raise RuntimeError('无法打开剪贴板')
        try:
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_UNICODETEXT, hglobal)
        finally:
            user32.CloseClipboard()
    except Exception:
        # Clipboard data was not handed off to the system: free the memory.
        kernel32.GlobalFree(hglobal)
        raise