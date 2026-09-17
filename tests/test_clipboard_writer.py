import pytest

from SystemTools import clipboard_writer


class TestLinuxFallback:
    def test_wl_copy_used_when_available(self, monkeypatch):
        monkeypatch.setattr(clipboard_writer.shutil, 'which', lambda cmd: '/usr/bin/wl-copy' if cmd == 'wl-copy' else None)
        calls = []
        monkeypatch.setattr(
            clipboard_writer.subprocess, 'run',
            lambda args, **kwargs: calls.append((args, kwargs)),
        )
        clipboard_writer._copy_to_clipboard_linux('hello')
        assert calls == [(['/usr/bin/wl-copy'], {'input': b'hello', 'check': True})]

    def test_xclip_used_when_only_x11(self, monkeypatch):
        def fake_which(cmd):
            if cmd == 'wl-copy':
                return None
            if cmd == 'xclip':
                return '/usr/bin/xclip'
            return None
        monkeypatch.setattr(clipboard_writer.shutil, 'which', fake_which)
        calls = []
        monkeypatch.setattr(
            clipboard_writer.subprocess, 'run',
            lambda args, **kwargs: calls.append((args, kwargs)),
        )
        clipboard_writer._copy_to_clipboard_linux('hi')
        assert calls == [(['/usr/bin/xclip', '-selection', 'clipboard'], {'input': b'hi', 'check': True})]

    def test_no_tool_raises(self, monkeypatch):
        monkeypatch.setattr(clipboard_writer.shutil, 'which', lambda cmd: None)
        with pytest.raises(RuntimeError, match='wl-clipboard'):
            clipboard_writer._copy_to_clipboard_linux('hi')

    def test_subprocess_failure_raises(self, monkeypatch):
        monkeypatch.setattr(clipboard_writer.shutil, 'which', lambda cmd: '/usr/bin/wl-copy' if cmd == 'wl-copy' else None)

        def boom(args, **kwargs):
            raise FileNotFoundError('wl-copy missing')
        monkeypatch.setattr(clipboard_writer.subprocess, 'run', boom)
        with pytest.raises(FileNotFoundError):
            clipboard_writer._copy_to_clipboard_linux('hi')


class TestDarwinFallback:
    def test_pbcopy_used(self, monkeypatch):
        monkeypatch.setattr(clipboard_writer.shutil, 'which', lambda cmd: '/usr/bin/pbcopy' if cmd == 'pbcopy' else None)
        calls = []
        monkeypatch.setattr(
            clipboard_writer.subprocess, 'run',
            lambda args, **kwargs: calls.append((args, kwargs)),
        )
        clipboard_writer._copy_to_clipboard_darwin('hi')
        assert calls == [(['/usr/bin/pbcopy'], {'input': b'hi', 'check': True})]

    def test_missing_pbcopy_raises(self, monkeypatch):
        monkeypatch.setattr(clipboard_writer.shutil, 'which', lambda cmd: None)
        with pytest.raises(RuntimeError, match='pbcopy'):
            clipboard_writer._copy_to_clipboard_darwin('hi')


class TestTkinterPrimary:
    def test_tkinter_success_returns_without_fallback(self, monkeypatch):
        calls = []

        class FakeTk:
            def __init__(self):
                self.clipboard = []

            def withdraw(self):
                calls.append('withdraw')

            def clipboard_clear(self):
                self.clipboard = []
                calls.append('clear')

            def clipboard_append(self, text):
                self.clipboard = [text]
                calls.append('append')

            def update(self):
                calls.append('update')

            def destroy(self):
                calls.append('destroy')

        fake = FakeTk()

        def fake_helper(text):
            root = fake
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()

        monkeypatch.setattr(clipboard_writer, '_copy_via_tkinter', fake_helper)
        clipboard_writer.copy_to_clipboard('abc')
        assert calls == ['withdraw', 'clear', 'append', 'update', 'destroy']
        assert fake.clipboard == ['abc']

    def test_tkinter_failure_falls_back_to_cli(self, monkeypatch):
        def broken_tk(*args, **kwargs):
            raise RuntimeError('no display available')
        import tkinter as _tk
        monkeypatch.setattr(_tk, 'Tk', broken_tk)
        monkeypatch.setattr(clipboard_writer.shutil, 'which', lambda cmd: '/usr/bin/wl-copy' if cmd == 'wl-copy' else None)
        calls = []
        monkeypatch.setattr(
            clipboard_writer.subprocess, 'run',
            lambda args, **kwargs: calls.append((args, kwargs)),
        )
        clipboard_writer.copy_to_clipboard('fallback text')
        assert calls == [(['/usr/bin/wl-copy'], {'input': b'fallback text', 'check': True})]


class TestWindows:
    def test_windows_helper_present(self):
        # Import-level guard: on non-Windows the names are simply absent,
        # but the module must import cleanly everywhere.
        assert hasattr(clipboard_writer, 'copy_to_clipboard_windows')