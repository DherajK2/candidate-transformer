"""
CLI and main entrypoint unit tests.
"""

from unittest.mock import patch
import pytest
from main import main


def test_cli_help():
    """Asserts that calling main with --help exits cleanly."""
    with patch("sys.argv", ["main.py", "--help"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0


def test_cli_missing_args():
    """Asserts that running main without inputs exits with an error code."""
    with patch("sys.argv", ["main.py"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
