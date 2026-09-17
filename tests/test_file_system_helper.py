
import pytest

from SystemTools.file_system_helper import create_dir_if_not_exists


class TestCreateDir:
    def test_creates_nested_dir(self, tmp_path):
        target = tmp_path / 'a' / 'b' / 'c'
        create_dir_if_not_exists(dir_path=str(target))
        assert target.is_dir()

    def test_existing_dir_is_ok(self, tmp_path):
        target = tmp_path / 'exists'
        target.mkdir()
        create_dir_if_not_exists(dir_path=str(target))  # must not raise
        assert target.is_dir()

    def test_file_path_creates_parent(self, tmp_path):
        file_path = tmp_path / 'logs' / 'app.log'
        create_dir_if_not_exists(file_path=str(file_path))
        assert (tmp_path / 'logs').is_dir()
        assert not file_path.exists()

    def test_both_args_raises(self, tmp_path):
        with pytest.raises(ValueError, match='Only one'):
            create_dir_if_not_exists(dir_path=str(tmp_path), file_path=str(tmp_path / 'f.txt'))

    def test_no_args_raises(self):
        with pytest.raises(ValueError, match='must be provided'):
            create_dir_if_not_exists()

    def test_os_error_propagates(self, tmp_path):
        # unwritable path: a file that pretends to be a directory
        blocker = tmp_path / 'blocker'
        blocker.write_text('i am a file')
        with pytest.raises(OSError):
            create_dir_if_not_exists(dir_path=str(blocker / 'sub'))