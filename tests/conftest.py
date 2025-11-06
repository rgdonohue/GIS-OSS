import sys
from pathlib import Path


def _add_src_to_path() -> None:
    """Ensure the src/ directory is importable during tests."""

    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


_add_src_to_path()
