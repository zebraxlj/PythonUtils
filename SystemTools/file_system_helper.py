import os
from typing import Optional


def create_dir_if_not_exists(dir_path: Optional[str] = None, file_path: Optional[str] = None) -> None:
    """Create a directory (or the parent directory of a file) if it does not exist.

    Exactly one of ``dir_path`` or ``file_path`` must be provided.

    Args:
        dir_path: Directory to create.
        file_path: Create the parent directory of this file path instead.

    Raises:
        ValueError: when both, or neither, of ``dir_path``/``file_path`` is given.
    """
    if dir_path and file_path:
        raise ValueError('Only one of dir_path or file_path should be provided.')
    if not dir_path and not file_path:
        raise ValueError('One of dir_path or file_path must be provided.')
    if file_path:
        dir_path = os.path.dirname(file_path)
    assert dir_path is not None  # guaranteed by the guards above
    os.makedirs(dir_path, exist_ok=True)
