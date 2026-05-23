from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAIL_LINE_LIMIT = 40
COMMAND_TIMEOUT_SECONDS = 180

FAKE_ENV = {
    "CHAT_PROVIDER": "openai_compatible",
    "CHAT_API_KEY": "fake-chat-key",
    "CHAT_BASE_URL": "https://api.example.test",
    "DASHSCOPE_API_KEY": "fake-dashscope-key",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}


@dataclass
class GateResult:
    name: str
    command: list[str]
    passed: bool
    return_code: int | None
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""
    timed_out: bool = False


def _tail(text: str, limit: int = TAIL_LINE_LIMIT) -> str:
    lines = (text or "").splitlines()
    return "\n".join(lines[-limit:])


def _display_command(command: Sequence[str]) -> str:
    return " ".join(command)


def _relative_existing(paths: Sequence[str]) -> list[str]:
    existing: list[str] = []
    for path_text in paths:
        path = PROJECT_ROOT / path_text
        if path.exists():
            existing.append(path_text)
    return existing


def _compile_targets() -> list[str]:
    targets = _relative_existing([
        "app.py",
        "config.py",
        "prompts.py",
        "schemas.py",
        "graph",
        "services",
        "utils",
        "vector_store",
        "evals",
    ])
    root_tests = sorted(
        path.name
        for path in PROJECT_ROOT.glob("test_*.py")
        if path.is_file()
    )
    return targets + root_tests


def _gate_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(FAKE_ENV)
    return env


def run_command(name: str, command: list[str]) -> GateResult:
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=_gate_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
        duration = round(time.perf_counter() - start, 2)
        return GateResult(
            name=name,
            command=command,
            passed=completed.returncode == 0,
            return_code=completed.returncode,
            duration_seconds=duration,
            stdout_tail=_tail(completed.stdout),
            stderr_tail=_tail(completed.stderr),
        )
    except subprocess.TimeoutExpired as exc:
        duration = round(time.perf_counter() - start, 2)
        return GateResult(
            name=name,
            command=command,
            passed=False,
            return_code=None,
            duration_seconds=duration,
            stdout_tail=_tail(exc.stdout or ""),
            stderr_tail=_tail(exc.stderr or ""),
            timed_out=True,
        )


def build_gate_commands() -> list[tuple[str, list[str]]]:
    compile_targets = _compile_targets()
    return [
        (
            "py_compile",
            [sys.executable, "-m", "compileall", "-q", *compile_targets],
        ),
        (
            "anti_assumption_eval",
            [sys.executable, "evals/anti_assumption_eval.py"],
        ),
        (
            "direction_choice",
            [sys.executable, "test_direction_choice.py"],
        ),
        (
            "smoke_check_local",
            [sys.executable, "evals/run_smoke_check.py", "--mode", "local"],
        ),
    ]


def _print_result(result: GateResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[{status}] {result.name} ({result.duration_seconds}s)")
    print(f"  command: {_display_command(result.command)}")
    if result.passed:
        return

    if result.timed_out:
        print(f"  timed_out: true ({COMMAND_TIMEOUT_SECONDS}s)")
    else:
        print(f"  return_code: {result.return_code}")
    if result.stdout_tail:
        print("  stdout_tail:")
        print(result.stdout_tail)
    if result.stderr_tail:
        print("  stderr_tail:")
        print(result.stderr_tail)


def main() -> int:
    print("AI Workflow Coach Regression Gate")
    print()
    print("Mode: local non-network regression")
    print("Fake env: CHAT_PROVIDER, CHAT_API_KEY, CHAT_BASE_URL, DASHSCOPE_API_KEY")
    print("Excluded: real smoke, P1 real quality eval, P2 RAG ablation, build_index")
    print()

    results = [
        run_command(name, command)
        for name, command in build_gate_commands()
    ]

    for result in results:
        _print_result(result)

    failed = [result for result in results if not result.passed]
    print()
    print("Summary:")
    print(f"- total: {len(results)}")
    print(f"- passed: {len(results) - len(failed)}")
    print(f"- failed: {len(failed)}")
    print("- failed_checks: " + ",".join(result.name for result in failed))
    print()
    print(f"Result: {'PASS' if not failed else 'FAIL'}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
