from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import unicodedata
from urllib.parse import parse_qs, urlparse
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_GITHUB_REPO = "MC-and-his-Agents/Syvert"
REPO_CANONICAL_GITHUB_REPOS = {
    "syvert": "MC-and-his-Agents/Syvert",
    "webenvoy": "MC-and-his-Agents/WebEnvoy",
}


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


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))


def syvert_state_dir() -> Path:
    return codex_home() / "state" / "syvert"


def syvert_state_file(name: str) -> Path:
    return syvert_state_dir() / name


def legacy_state_file(name: str) -> Path:
    return codex_home() / "state" / name


def now_iso_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_github_repo_from_remote_url(origin_url: str) -> str | None:
    normalized = origin_url.strip()
    if not normalized:
        return None
    https_match = re.match(r"^https://github\.com/([^/]+/[^/]+?)(?:\.git)?$", normalized)
    if https_match:
        return https_match.group(1)
    ssh_match = re.match(r"^git@github\.com:([^/]+/[^/]+?)(?:\.git)?$", normalized)
    if ssh_match:
        return ssh_match.group(1)
    ssh_url_match = re.match(r"^ssh://git@github\.com(?::\d+)?/([^/]+/[^/]+?)(?:\.git)?/?$", normalized)
    if ssh_url_match:
        return ssh_url_match.group(1)
    return None


@lru_cache(maxsize=1)
def default_github_repo() -> str:
    configured = os.environ.get("SYVERT_GITHUB_REPO", "").strip()
    if configured and re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", configured):
        return configured
    repo_names = [REPO_ROOT.name.strip().casefold()]
    git_entry = REPO_ROOT / ".git"
    if git_entry.is_file():
        try:
            gitdir_line = git_entry.read_text(encoding="utf-8").strip()
        except OSError:
            gitdir_line = ""
        if gitdir_line.lower().startswith("gitdir:"):
            gitdir_path = Path(gitdir_line.split(":", 1)[1].strip())
            if not gitdir_path.is_absolute():
                gitdir_path = (REPO_ROOT / gitdir_path).resolve()
            for parent in gitdir_path.parents:
                if parent.name == ".git":
                    repo_names.append(parent.parent.name.strip().casefold())
                    break
    for repo_name in repo_names:
        if repo_name in REPO_CANONICAL_GITHUB_REPOS:
            return REPO_CANONICAL_GITHUB_REPOS[repo_name]
        for canonical_name, canonical_repo in REPO_CANONICAL_GITHUB_REPOS.items():
            if repo_name.startswith(f"{canonical_name}-"):
                return canonical_repo
    completed = run(["git", "remote", "get-url", "origin"], cwd=REPO_ROOT, check=False)
    if completed.returncode == 0:
        parsed = parse_github_repo_from_remote_url(completed.stdout.strip())
        if parsed:
            parsed_name = parsed.split("/", 1)[1].strip().casefold()
            if parsed_name in REPO_CANONICAL_GITHUB_REPOS:
                return REPO_CANONICAL_GITHUB_REPOS[parsed_name]
    return CANONICAL_GITHUB_REPO


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    tokens = re.findall(r"[a-z0-9]+", normalized.lower())
    return "-".join(tokens) or "task"


def integration_ref_is_checkable(value: str) -> bool:
    normalized = value.strip()
    if not normalized or normalized.lower() == "none":
        return False
    if re.match(r"^#\d+$", normalized):
        return True
    if re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#\d+$", normalized):
        return True
    if re.match(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/\d+$", normalized):
        return True
    parsed = urlparse(normalized)
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        return False
    if len(path_parts) < 4 or path_parts[0] != "orgs" or path_parts[2] != "projects":
        return False
    item_ids = parse_qs(parsed.query).get("itemId", [])
    return bool(item_ids and str(item_ids[0]).strip())


def normalize_integration_ref_for_comparison(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    if normalized.lower() == "none":
        return "none"

    local_issue_match = re.match(r"^#(\d+)$", normalized)
    if local_issue_match:
        return f"issue:{default_github_repo().lower()}#{local_issue_match.group(1)}"

    repo_issue_match = re.match(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)$", normalized)
    if repo_issue_match:
        return f"issue:{repo_issue_match.group(1).lower()}#{repo_issue_match.group(2)}"

    issue_url_match = re.match(r"^https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(\d+)$", normalized)
    if issue_url_match:
        return f"issue:{issue_url_match.group(1).lower()}#{issue_url_match.group(2)}"

    parsed = urlparse(normalized)
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme == "https" and parsed.netloc.lower() == "github.com" and len(path_parts) >= 4:
        if path_parts[0] == "orgs" and path_parts[2] == "projects":
            item_ids = parse_qs(parsed.query).get("itemId", [])
            if item_ids:
                organization = path_parts[1].lower()
                project_number = path_parts[3]
                return f"project-item:{organization}/{project_number}#{item_ids[0]}"

    return normalized
