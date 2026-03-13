"""Tests for file I/O tools."""

import pytest
from pathlib import Path

from factory.tools.file_io import make_write_file, make_read_file, make_list_files


def test_write_and_read(tmp_workspace: Path):
    write = make_write_file(tmp_workspace)
    read = make_read_file(tmp_workspace)

    result = write("test.py", "print('hello')")
    assert "Wrote" in result

    content = read("test.py")
    assert "print('hello')" in content


def test_write_nested(tmp_workspace: Path):
    write = make_write_file(tmp_workspace)
    write("sub/dir/script.py", "x = 1")
    assert (tmp_workspace / "sub" / "dir" / "script.py").exists()


def test_read_missing(tmp_workspace: Path):
    read = make_read_file(tmp_workspace)
    result = read("nonexistent.py")
    assert "not found" in result.lower()


def test_sandbox_escape_write(tmp_workspace: Path):
    write = make_write_file(tmp_workspace)
    with pytest.raises(ValueError, match="sandbox"):
        write("../../etc/evil.py", "bad")


def test_sandbox_escape_read(tmp_workspace: Path):
    read = make_read_file(tmp_workspace)
    # Should not be able to read outside workspace
    with pytest.raises(ValueError, match="sandbox"):
        read("../../etc/passwd")


def test_list_files(tmp_workspace: Path):
    write = make_write_file(tmp_workspace)
    write("a.py", "1")
    write("sub/b.py", "2")

    list_files = make_list_files(tmp_workspace)
    output = list_files()
    assert "a.py" in output
    assert "b.py" in output


def test_list_empty(tmp_workspace: Path):
    list_files = make_list_files(tmp_workspace)
    output = list_files()
    # Should show at least the directory itself
    assert output


def test_read_truncation(tmp_workspace: Path):
    write = make_write_file(tmp_workspace)
    write("big.txt", "x" * 10000)

    read = make_read_file(tmp_workspace)
    content = read("big.txt")
    assert "truncated" in content.lower()
