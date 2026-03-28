from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent


class CommandError(RuntimeError):
    """Raised when a subprocess command fails."""

    def __init__(self, cmd: Sequence[str], message: str, stdout: str = "", stderr: str = "") -> None:
        self.cmd = list(cmd)
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(message)


def repo_root() -> Path:
    return REPO_ROOT


def ensure_repo_root_on_path() -> None:
    root_text = str(REPO_ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


def run(
    cmd: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(cmd),
        cwd=str(cwd or REPO_ROOT),
        env=env,
        text=True,
        capture_output=capture_output,
        check=False,
    )
    if check and completed.returncode != 0:
        joined = " ".join(shlex.quote(part) for part in cmd)
        message = f"命令失败: {joined}"
        raise CommandError(cmd, message, completed.stdout, completed.stderr)
    return completed


def require_cli(name: str) -> None:
    from shutil import which

    if which(name) is None:
        raise SystemExit(f"缺少依赖命令: {name}")


def git_changed_files(base_ref: str, head_ref: str = "HEAD", *, repo: Path | None = None) -> list[str]:
    repo_dir = repo or REPO_ROOT
    completed = run(
        ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"],
        cwd=repo_dir,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        if "no merge base" in stderr:
            fallback = run(
                ["git", "diff", "--name-only", base_ref, head_ref],
                cwd=repo_dir,
                check=False,
            )
            if fallback.returncode == 0:
                return [line.strip() for line in fallback.stdout.splitlines() if line.strip()]
        raise SystemExit(stderr or f"无法比较 {base_ref}...{head_ref}")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def git_current_branch(*, repo: Path | None = None) -> str:
    completed = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo or REPO_ROOT)
    return completed.stdout.strip()


def git_fetch_branch(branch: str, *, repo: Path | None = None) -> None:
    run(["git", "fetch", "origin", branch], cwd=repo or REPO_ROOT, check=False)


def git_ls_files(patterns: Sequence[str] | None = None, *, repo: Path | None = None) -> list[str]:
    cmd = ["git", "ls-files"]
    if patterns:
        cmd.extend(patterns)
    completed = run(cmd, cwd=repo or REPO_ROOT)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: object) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def format_changed_files(files: Iterable[str]) -> str:
    lines = [f"- `{path}`" for path in files]
    return "\n".join(lines) if lines else "- 无"


def bool_text(value: bool) -> str:
    return "是" if value else "否"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def relative_to_repo(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def repo_relative_from_text(text: str) -> Path:
    return (REPO_ROOT / text).resolve()


def parse_pr_class_from_body(body: str) -> str:
    for line in body.splitlines():
        if "PR Class:" in line:
            return line.split("PR Class:", 1)[1].strip(" `")
    return ""


def env_with_repo_pythonpath(env: dict[str, str] | None = None) -> dict[str, str]:
    merged = dict(os.environ)
    if env:
        merged.update(env)
    pythonpath = merged.get("PYTHONPATH", "")
    repo_text = str(REPO_ROOT)
    merged["PYTHONPATH"] = repo_text if not pythonpath else f"{repo_text}{os.pathsep}{pythonpath}"
    return merged
