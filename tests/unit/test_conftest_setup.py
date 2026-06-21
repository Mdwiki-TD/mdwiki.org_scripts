"""
Unit tests for the module-level environment setup in tests/conftest.py.

Specifically covers the MAIN_DIR environment variable initialization added
in this PR: setting it to str(Path(tempfile.gettempdir()) / "test").
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


class TestMainDirEnvVar:
    """Tests for the MAIN_DIR environment variable set in conftest.py."""

    def test_main_dir_is_set(self):
        """MAIN_DIR must be present in os.environ after conftest is loaded."""
        assert "MAIN_DIR" in os.environ

    def test_main_dir_is_string(self):
        """MAIN_DIR value must be a plain string, not a Path or other type."""
        assert isinstance(os.environ["MAIN_DIR"], str)

    def test_main_dir_equals_expected_path(self):
        """MAIN_DIR must equal str(Path(tempfile.gettempdir()) / 'test')."""
        expected = str(Path(tempfile.gettempdir()) / "test")
        assert os.environ["MAIN_DIR"] == expected

    def test_main_dir_ends_with_test_segment(self):
        """MAIN_DIR must end with the 'test' path segment."""
        main_dir = os.environ["MAIN_DIR"]
        # Use Path to check the final component so the test is OS-agnostic.
        assert Path(main_dir).name == "test"

    def test_main_dir_parent_is_system_temp(self):
        """The parent of MAIN_DIR must be the system temporary directory."""
        main_dir = Path(os.environ["MAIN_DIR"])
        assert main_dir.parent == Path(tempfile.gettempdir())

    def test_main_dir_not_equal_to_raw_tempdir(self):
        """MAIN_DIR must not be set to the bare temp dir (regression: missing /test)."""
        system_temp = str(Path(tempfile.gettempdir()))
        assert os.environ["MAIN_DIR"] != system_temp

    def test_main_dir_contains_test_subdirectory(self):
        """MAIN_DIR must include a 'test' subdirectory under the temp dir."""
        main_dir = os.environ["MAIN_DIR"]
        system_temp = str(Path(tempfile.gettempdir()))
        assert main_dir.startswith(system_temp)
        assert main_dir != system_temp

    def test_main_dir_path_segment_is_exactly_test(self):
        """MAIN_DIR final segment must be exactly 'test', not 'testing' or 'tmp'."""
        final_segment = Path(os.environ["MAIN_DIR"]).name
        assert final_segment == "test"
        assert final_segment != "testing"
        assert final_segment != "tmp"
