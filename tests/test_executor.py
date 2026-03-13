"""Tests for the code executor tool."""

from pathlib import Path

from factory.tools.executor import execute_script, make_execute_code


def test_execute_passing_script(sample_script: Path, tmp_workspace: Path):
    result = execute_script(sample_script, tmp_workspace, timeout=10)
    assert result.exit_code == 0
    assert "hello world" in result.stdout
    assert not result.timed_out


def test_execute_failing_script(failing_script: Path, tmp_workspace: Path):
    result = execute_script(failing_script, tmp_workspace, timeout=10)
    assert result.exit_code != 0
    assert "ValueError" in result.stderr
    assert not result.timed_out


def test_execute_timeout(tmp_workspace: Path):
    script = tmp_workspace / "slow.py"
    script.write_text("import time; time.sleep(60)\n")
    result = execute_script(script, tmp_workspace, timeout=2)
    assert result.timed_out
    assert result.exit_code == -1


def test_execute_missing_script(tmp_workspace: Path):
    result = execute_script(tmp_workspace / "nope.py", tmp_workspace)
    assert result.exit_code == 1
    assert "not found" in result.stderr


def test_make_execute_code_tool(sample_script: Path, tmp_workspace: Path):
    execute_code = make_execute_code(tmp_workspace, timeout=10)
    output = execute_code("script.py")
    assert "Exit code: 0" in output
    assert "hello world" in output


def test_execute_code_sandbox(tmp_workspace: Path):
    execute_code = make_execute_code(tmp_workspace, timeout=10)
    output = execute_code("../../etc/passwd")
    assert "Error" in output or "not found" in output.lower()
