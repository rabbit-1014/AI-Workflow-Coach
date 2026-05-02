import subprocess

from evals import run_smoke_check


class FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_command_success(monkey_patch=None):
    original_run = subprocess.run

    def fake_run(*args, **kwargs):
        return FakeCompletedProcess(returncode=0, stdout="ok", stderr="")

    subprocess.run = fake_run
    try:
        result = run_smoke_check.run_command("fake_success", ["python", "fake.py"])
    finally:
        subprocess.run = original_run

    assert result["passed"] is True
    assert result["return_code"] == 0
    assert "duration_seconds" in result


def test_run_command_failure_keeps_tail():
    original_run = subprocess.run
    long_stdout = "\n".join(f"stdout-{index}" for index in range(60))
    long_stderr = "\n".join(f"stderr-{index}" for index in range(60))

    def fake_run(*args, **kwargs):
        return FakeCompletedProcess(returncode=1, stdout=long_stdout, stderr=long_stderr)

    subprocess.run = fake_run
    try:
        result = run_smoke_check.run_command("fake_failure", ["python", "fake.py"])
    finally:
        subprocess.run = original_run

    assert result["passed"] is False
    assert result["return_code"] == 1
    assert "stdout-20" in result["stdout_tail"]
    assert "stdout-19" not in result["stdout_tail"]
    assert "stderr-20" in result["stderr_tail"]
    assert "stderr-19" not in result["stderr_tail"]


def test_summary_counts_are_correct():
    summary = run_smoke_check.summarize_results([
        {"passed": True, "duration_seconds": 1},
        {"passed": True, "duration_seconds": 2},
        {"passed": False, "duration_seconds": 3},
    ])

    assert summary["total"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["overall_passed"] is False
    assert summary["duration_seconds"] == 6


def test_local_mode_excludes_real_api_scripts():
    commands = run_smoke_check.build_local_test_commands()
    command_text = "\n".join(" ".join(command) for _, command in commands)

    assert "test_deepseek_call.py" not in command_text
    assert "test_rag.py" not in command_text
    assert "run_content_eval.py --mode real" not in command_text


if __name__ == "__main__":
    test_run_command_success()
    test_run_command_failure_keeps_tail()
    test_summary_counts_are_correct()
    test_local_mode_excludes_real_api_scripts()
    print("test_smoke_check_runner.py: all tests passed")
