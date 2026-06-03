"""Fast Downward integration."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from .config import Settings
from .models import PlannerResult


class FastDownwardPlanner:
    def __init__(self, settings: Settings):
        self.settings = settings

    def build_command(self, domain_path: Path, problem_path: Path) -> list[str]:
        configured = self.settings.fast_downward_path.strip()
        if not configured:
            return []
        configured_path = Path(configured).expanduser()
        if configured_path.exists():
            command = [sys.executable, str(configured_path)] if str(configured_path).endswith(".py") else [str(configured_path)]
        else:
            parts = shlex.split(configured)
            if len(parts) > 1:
                command = parts
            elif configured.endswith(".py"):
                command = [sys.executable, configured]
            else:
                command = [configured]
        command.extend([str(domain_path), str(problem_path), "--search", self.settings.search])
        return command

    def plan(self, domain_path: Path, problem_path: Path, work_dir: Path) -> PlannerResult:
        command = self.build_command(domain_path, problem_path)
        log_path = work_dir / "planner.log"
        if not command:
            return PlannerResult(
                success=False,
                log_path=log_path,
                error="FAST_DOWNWARD_PATH is not configured.",
            )

        work_dir.mkdir(parents=True, exist_ok=True)
        start = time.perf_counter()
        try:
            process = subprocess.run(
                command,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=self.settings.max_planning_time,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            duration = time.perf_counter() - start
            output = process.stdout + ("\n" + process.stderr if process.stderr else "")
            log_path.write_text(output, encoding="utf-8")
            plan_path = _find_plan_file(work_dir)
            plan = _read_plan(plan_path) if plan_path else parse_plan_from_output(output)
            success = bool(plan) or "Solution found" in output or process.returncode == 0 and "Plan length: 0" in output
            return PlannerResult(
                success=success,
                plan=plan,
                stdout=process.stdout,
                stderr=process.stderr,
                return_code=process.returncode,
                duration_sec=duration,
                plan_path=plan_path,
                log_path=log_path,
                command=command,
                error="" if success else "Planner did not produce a plan.",
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - start
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            log_path.write_text(stdout + "\n" + stderr, encoding="utf-8")
            return PlannerResult(
                success=False,
                stdout=stdout,
                stderr=stderr,
                duration_sec=duration,
                log_path=log_path,
                command=command,
                error=f"Planner timed out after {self.settings.max_planning_time} seconds.",
            )
        except OSError as exc:
            return PlannerResult(
                success=False,
                log_path=log_path,
                command=command,
                error=f"Planner execution failed: {exc}",
            )


def parse_plan_from_output(output: str) -> list[str]:
    plan: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("(") and line.endswith(")"):
            plan.append(line)
    return plan


def _find_plan_file(work_dir: Path) -> Path | None:
    candidates = sorted(
        [path for path in work_dir.iterdir() if path.name.startswith("sas_plan")],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _read_plan(plan_path: Path) -> list[str]:
    plan = []
    for raw_line in plan_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("(") and line.endswith(")"):
            plan.append(line)
        else:
            plan.append(f"({line})")
    return plan


def planner_available(settings: Settings) -> bool:
    if not settings.fast_downward_path:
        return False
    first = shlex.split(settings.fast_downward_path)[0]
    return bool(Path(first).expanduser().exists() or os.access(first, os.X_OK))
