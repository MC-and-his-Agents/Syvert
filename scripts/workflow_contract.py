from __future__ import annotations

import os
from pathlib import Path

from scripts.common import REPO_ROOT


WORKFLOW_PATH = REPO_ROOT / "WORKFLOW.md"
DEFAULT_WORKSPACE_ROOT = Path("~/code/worktrees/syvert").expanduser()
REQUIRED_TOP_LEVEL_KEYS = ("tracker", "workspace", "agent", "codex")
REQUIRED_BODY_HEADINGS = (
    ("## 任务输入来源",),
    ("## worktree / bootstrap 规则", "## Worktree / Bootstrap 规则"),
    ("## checkpoint / resume / compact 规则", "## Checkpoint / Resume / Compact 规则"),
    ("## stop conditions", "## Stop Conditions"),
    ("## 何时必须更新 `exec-plan` / `TODO`", "## 何时必须更新 exec-plan / TODO"),
    ("## 何时允许进入 `open_pr` / `merge_pr`", "## 何时允许进入 open_pr / merge_pr"),
)


class WorkflowContractError(ValueError):
    pass


def split_front_matter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise WorkflowContractError("WORKFLOW.md 缺少 YAML front matter 起始分隔符。")
    marker = "\n---\n"
    end = text.find(marker, 4)
    if end == -1:
        raise WorkflowContractError("WORKFLOW.md 缺少 YAML front matter 结束分隔符。")
    return text[4:end], text[end + len(marker) :]


def parse_scalar(value: str) -> str | int:
    if value.isdigit():
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_front_matter(front_matter: str) -> dict:
    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]

    for lineno, raw_line in enumerate(front_matter.splitlines(), start=2):
        if not raw_line.strip():
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2 != 0:
            raise WorkflowContractError(f"front matter 第 {lineno} 行缩进必须是 2 的倍数。")

        line = raw_line.strip()
        if ":" not in line:
            raise WorkflowContractError(f"front matter 第 {lineno} 行缺少 `:`。")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            raise WorkflowContractError(f"front matter 第 {lineno} 行键名不能为空。")

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if raw_value == "":
            child: dict[str, object] = {}
            parent[key] = child
            stack.append((indent, child))
            continue

        parent[key] = parse_scalar(raw_value)

    return root


def load_workflow_contract(path: Path = WORKFLOW_PATH) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    front_matter, body = split_front_matter(text)
    contract = parse_front_matter(front_matter)
    return contract, body


def validate_workflow_contract(contract: dict, body: str) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in contract:
            errors.append(f"front matter 缺少顶层键 `{key}`")

    tracker = contract.get("tracker")
    if not isinstance(tracker, dict):
        errors.append("`tracker` 必须是对象。")
    else:
        if tracker.get("kind") != "github":
            errors.append("`tracker.kind` 必须为 `github`。")
        if tracker.get("scope") != "current-repo":
            errors.append("`tracker.scope` 必须为 `current-repo`。")

    workspace = contract.get("workspace")
    if not isinstance(workspace, dict):
        errors.append("`workspace` 必须是对象。")
    else:
        if not isinstance(workspace.get("root"), str):
            errors.append("`workspace.root` 必须是字符串。")
        if workspace.get("naming") != "issue-{number}-{slug}":
            errors.append("`workspace.naming` 必须为 `issue-{number}-{slug}`。")

    agent = contract.get("agent")
    if not isinstance(agent, dict):
        errors.append("`agent` 必须是对象。")
    else:
        max_turns = agent.get("max_turns")
        if not isinstance(max_turns, int) or max_turns <= 0:
            errors.append("`agent.max_turns` 必须是正整数。")

    codex = contract.get("codex")
    if not isinstance(codex, dict):
        errors.append("`codex` 必须是对象。")
    else:
        if codex.get("thread_sandbox") != "workspace-write":
            errors.append("`codex.thread_sandbox` 必须为 `workspace-write`。")
        if not isinstance(codex.get("approval_policy"), str) or not str(codex.get("approval_policy")).strip():
            errors.append("`codex.approval_policy` 必须是非空字符串。")

    for heading_group in REQUIRED_BODY_HEADINGS:
        if not any(heading in body for heading in heading_group):
            errors.append(f"正文缺少必需段落 `{' / '.join(heading_group)}`")

    return errors


def resolve_workspace_root(contract: dict, env: dict[str, str] | None = None) -> Path:
    workspace = contract.get("workspace") or {}
    raw_root = str(workspace.get("root", "$SYVERT_WORKSPACE_ROOT"))
    environment = os.environ if env is None else env
    if raw_root == "$SYVERT_WORKSPACE_ROOT":
        configured = environment.get("SYVERT_WORKSPACE_ROOT")
        return Path(configured).expanduser() if configured else DEFAULT_WORKSPACE_ROOT
    return Path(os.path.expandvars(raw_root)).expanduser()


def render_workspace_key(issue_number: int, slug: str, contract: dict) -> str:
    naming = str((contract.get("workspace") or {}).get("naming", "issue-{number}-{slug}"))
    try:
        return naming.format(number=issue_number, slug=slug)
    except KeyError as exc:
        raise WorkflowContractError(f"`workspace.naming` 包含未知占位符: {exc}") from exc
