#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

from scripts.common import REPO_ROOT, bool_text, dump_json, ensure_parent, format_changed_files, load_json, require_cli, run
from scripts.item_context import active_exec_plans_for_issue, load_item_context_from_exec_plan, parse_item_context_from_body
from scripts.state_paths import guardian_legacy_state_path, guardian_state_path


SCHEMA_PATH = REPO_ROOT / "scripts" / "policy" / "pr_review_result_schema.json"
CODE_REVIEW_PATH = "code_review.md"
DEFAULT_STATE_FILE = guardian_state_path()
VALID_VERDICTS = {"APPROVE", "REQUEST_CHANGES"}
REVIEW_REQUIRED_BODY_FIELDS = ("issue", "item_key", "item_type", "release", "sprint")
REVIEW_EXECUTION_RULES = (
    "工件完整性只用于确认输入是否足够，不要把 checks、Draft 状态或 merge 动作当成 reviewer 结论来源。",
    "若缺少必要工件或验证证据，应明确指出阻断项；merge gate、head 绑定与 squash merge 安全性由 guardian gate 入口单独消费。",
)
REVIEW_SECTION_ALIASES = {
    "摘要": "summary",
    "Issue 摘要": "issue_summary",
    "关联事项": "item_context",
    "风险": "risk",
    "风险级别": "risk",
    "验证": "validation",
    "回滚": "rollback",
}
RAW_BODY_NOISE_HEADINGS = {"变更文件", "检查清单"}
REVIEW_GUIDE_HEADINGS = (
    "## 工件完整性检查",
    "## Review Rubric",
    "## 事项分级视角",
    "## 职责边界说明",
)
ISSUE_CONTEXT_HEADINGS = ("Goal", "Scope", "Required Outcomes", "Acceptance", "Acceptance Criteria", "Out of Scope", "Dependency")


def codex_review_timeout_seconds() -> int | None:
    raw_value = os.environ.get("SYVERT_GUARDIAN_TIMEOUT_SECONDS")
    if raw_value is None:
        return None
    value = raw_value.strip()
    if not value:
        return None
    try:
        timeout_seconds = int(value)
    except ValueError as exc:
        raise SystemExit("SYVERT_GUARDIAN_TIMEOUT_SECONDS 必须是正整数；留空或不设置表示不限制超时。") from exc
    if timeout_seconds <= 0:
        raise SystemExit("SYVERT_GUARDIAN_TIMEOUT_SECONDS 必须是正整数；留空或不设置表示不限制超时。")
    return timeout_seconds


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="执行 Syvert PR guardian 审查。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser("review", help="执行只读审查")
    review.add_argument("pr_number", type=int)
    review.add_argument("--post-review", action="store_true")
    review.add_argument("--json-output")

    merge = subparsers.add_parser("merge-if-safe", help="审查通过后执行 squash merge")
    merge.add_argument("pr_number", type=int)
    merge.add_argument("--post-review", action="store_true")
    merge.add_argument("--delete-branch", action="store_true")
    merge.add_argument("--refresh-review", action="store_true")

    return parser.parse_args(argv)


def require_auth() -> None:
    require_cli("gh")
    require_cli("codex")
    run(["gh", "auth", "status"], cwd=REPO_ROOT)


def pr_meta(pr_number: int) -> dict:
    completed = run(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            "number,title,body,url,isDraft,baseRefName,headRefName,headRefOid,author",
        ],
        cwd=REPO_ROOT,
    )
    return json.loads(completed.stdout)


def prepare_worktree(pr_number: int, meta: dict) -> tuple[Path, Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix="syvert-pr-guardian-"))
    worktree_dir = temp_dir / "worktree"
    base_ref = meta["baseRefName"]

    run(["git", "fetch", "origin", base_ref], cwd=REPO_ROOT, check=False)
    run(["git", "fetch", "origin", f"pull/{pr_number}/head:refs/remotes/origin/pr/{pr_number}"], cwd=REPO_ROOT)
    run(["git", "worktree", "add", "--detach", str(worktree_dir), f"origin/pr/{pr_number}"], cwd=REPO_ROOT)
    return temp_dir, worktree_dir


def cleanup(temp_dir: Path) -> None:
    worktree_dir = temp_dir / "worktree"
    if worktree_dir.exists():
        run(["git", "worktree", "remove", "--force", str(worktree_dir)], cwd=REPO_ROOT, check=False)
    shutil.rmtree(temp_dir, ignore_errors=True)


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_guardian_payload(meta: dict, result: dict) -> dict:
    return {
        "schema_version": 1,
        "pr_number": meta["number"],
        "head_sha": meta["headRefOid"],
        "verdict": result["verdict"],
        "safe_to_merge": result["safe_to_merge"],
        "summary": result["summary"],
        "reviewed_at": now_iso_utc(),
    }


def load_guardian_state(path: Path = DEFAULT_STATE_FILE) -> dict:
    if path.exists():
        return load_json(path)
    legacy_path = guardian_legacy_state_path()
    if path == DEFAULT_STATE_FILE and legacy_path.exists():
        return load_json(legacy_path)
    return {"prs": {}}


def save_guardian_result(pr_number: int, payload: dict, *, path: Path = DEFAULT_STATE_FILE) -> None:
    ensure_parent(path)
    state = load_guardian_state(path)
    state.setdefault("prs", {})[str(pr_number)] = payload
    dump_json(path, state)


def valid_guardian_payload(payload: object, *, pr_number: int, head_sha: str) -> dict | None:
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != 1:
        return None
    if payload.get("pr_number") != pr_number:
        return None
    if payload.get("head_sha") != head_sha:
        return None
    if payload.get("verdict") not in VALID_VERDICTS:
        return None
    if not isinstance(payload.get("safe_to_merge"), bool):
        return None
    if not isinstance(payload.get("summary"), str):
        return None
    if not isinstance(payload.get("reviewed_at"), str):
        return None
    return payload


def local_guardian_result(pr_number: int, head_sha: str, *, path: Path = DEFAULT_STATE_FILE) -> dict | None:
    payload = load_guardian_state(path).get("prs", {}).get(str(pr_number))
    return valid_guardian_payload(payload, pr_number=pr_number, head_sha=head_sha)


def find_latest_guardian_result(pr_number: int, head_sha: str, *, path: Path = DEFAULT_STATE_FILE) -> dict | None:
    return local_guardian_result(pr_number, head_sha, path=path)


def parse_all_markdown_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_heading: str | None = None
    preamble: list[str] = []

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if current_heading == "Issue 摘要" and heading in ISSUE_CONTEXT_HEADINGS:
                sections.setdefault(current_heading, []).append(line.rstrip())
                continue
            current_heading = heading
            sections.setdefault(current_heading, [])
            continue
        if current_heading is None:
            preamble.append(line.rstrip())
            continue
        if current_heading:
            sections[current_heading].append(line.rstrip())

    payload = {key: "\n".join(value).strip() for key, value in sections.items() if "\n".join(value).strip()}
    preamble_text = "\n".join(preamble).strip()
    if preamble_text:
        payload["__preamble__"] = preamble_text
    return payload


def parse_markdown_sections(body: str) -> dict[str, str]:
    raw_sections = parse_all_markdown_sections(body)
    sections: dict[str, str] = {}
    for heading, content in raw_sections.items():
        key = REVIEW_SECTION_ALIASES.get(heading)
        if key and content:
            sections[key] = content
    return sections


def extract_reviewer_rubric_excerpt(text: str) -> str:
    lines = text.splitlines()
    selected: list[str] = []
    active = False
    allowed = set(REVIEW_GUIDE_HEADINGS)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            active = stripped in allowed
        if active:
            selected.append(line)

    excerpt = "\n".join(selected).strip()
    if excerpt:
        return excerpt
    return "未能从 `code_review.md` 提取 reviewer rubric 节选，请围绕当前 diff、工件完整性与职责边界执行审查。"


def load_reviewer_rubric_excerpt(worktree_dir: Path, base_ref: str) -> str:
    completed = run(
        ["git", "show", f"origin/{base_ref}:{CODE_REVIEW_PATH}"],
        cwd=worktree_dir,
        check=False,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return extract_reviewer_rubric_excerpt(completed.stdout)

    path = worktree_dir / CODE_REVIEW_PATH
    if path.exists():
        return extract_reviewer_rubric_excerpt(path.read_text(encoding="utf-8"))
    return "未找到 `code_review.md`，请按当前变更与最小必要上下文执行 reviewer rubric 审查。"


def extract_named_markdown_sections(body: str, headings: tuple[str, ...]) -> dict[str, str]:
    selected = set(headings)
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            current = heading if heading in selected else None
            if current:
                sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line.rstrip())

    return {key: "\n".join(value).strip() for key, value in sections.items() if "\n".join(value).strip()}


def fetch_issue_context(issue_number: int) -> dict[str, object]:
    completed = run(
        ["gh", "issue", "view", str(issue_number), "--json", "number,title,body,url"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "identity": [f"- Issue: #{issue_number}", "- issue 上下文暂不可用"],
            "summary": "issue 内容暂不可用。",
        }

    payload = json.loads(completed.stdout or "{}")
    body = str(payload.get("body") or "").strip()
    identity = [
        f"- Issue: #{payload.get('number', issue_number)}",
        f"- 标题: {payload.get('title', '')}",
        f"- 链接: {payload.get('url', '')}",
    ]
    sections = extract_named_markdown_sections(body, ISSUE_CONTEXT_HEADINGS)
    if sections:
        summary_parts: list[str] = []
        for heading in ISSUE_CONTEXT_HEADINGS:
            content = sections.get(heading)
            if not content:
                continue
            summary_parts.extend([f"## {heading}", content, ""])
        summary = "\n".join(summary_parts).strip()
    else:
        summary = body or "无 issue 正文。"
    return {"identity": identity, "summary": summary}


def fetch_diff_stats(worktree_dir: Path, base_ref: str) -> tuple[list[str], str]:
    changed = run(
        ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
        cwd=worktree_dir,
        check=False,
    )
    if changed.returncode != 0:
        raise SystemExit(changed.stderr.strip() or f"无法比较 origin/{base_ref}...HEAD")
    changed_files = [line.strip() for line in changed.stdout.splitlines() if line.strip()]

    diff_stat = run(
        ["git", "diff", "--stat", "--compact-summary", f"origin/{base_ref}...HEAD"],
        cwd=worktree_dir,
        check=False,
    )
    stat_text = diff_stat.stdout.strip() if diff_stat.returncode == 0 else ""
    return changed_files, stat_text or "无 diff stat。"


def extract_related_links_from_exec_plan(exec_plan_path: Path) -> list[str]:
    links = [exec_plan_path.as_posix()]
    patterns = (
        re.compile(r"^- 关联 spec[:：]\s*`?([^`]+)`?\s*$"),
        re.compile(r"^- 关联 decision[:：]\s*`?([^`]+)`?\s*$"),
    )
    for raw_line in exec_plan_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        for pattern in patterns:
            match = pattern.match(stripped)
            if not match:
                continue
            value = match.group(1).strip()
            if not value or value.startswith("无"):
                continue
            if "/" in value or value.endswith(".md"):
                links.append(value)
    return links


def build_item_context_summary(meta: dict, repo_root: Path) -> tuple[dict[str, str], list[str], list[str]]:
    body_context = parse_item_context_from_body(str(meta.get("body") or ""))
    notes: list[str] = []
    related_paths: list[str] = []

    missing = [field for field in REVIEW_REQUIRED_BODY_FIELDS if not body_context.get(field, "").strip()]
    if missing:
        notes.append(f"PR 正文缺少完整事项上下文字段：{', '.join(missing)}。")
        return body_context, notes, related_paths

    issue_text = body_context.get("issue", "").strip()
    try:
        issue_number = int(issue_text)
    except ValueError:
        notes.append("PR 正文中的 Issue 字段不是合法数字。")
        return body_context, notes, related_paths

    item_key = body_context["item_key"]
    exec_plan = load_item_context_from_exec_plan(repo_root, item_key)
    if exec_plan.get("conflict") == "duplicate_metadata_keys":
        notes.append("active exec-plan 元数据存在重复键，无法确认唯一事项上下文。")
        return body_context, notes, related_paths
    if exec_plan.get("conflict") == "multiple_active_exec_plans":
        notes.append("当前 item_key 命中多个 active exec-plan。")
        return body_context, notes, related_paths
    if not exec_plan:
        notes.append("当前 item_key 未找到 active exec-plan。")
        return body_context, notes, related_paths

    exec_plan_path = Path(exec_plan.get("exec_plan", ""))
    if exec_plan_path:
        if not exec_plan_path.is_absolute():
            exec_plan_path = repo_root / exec_plan_path
        related_paths.extend(extract_related_links_from_exec_plan(exec_plan_path))

    issue_exec_plans = active_exec_plans_for_issue(repo_root, issue_number)
    if len(issue_exec_plans) != 1:
        notes.append(f"当前 Issue 命中的 active exec-plan 数量异常：{len(issue_exec_plans)}。")
        return body_context, notes, related_paths
    if issue_exec_plans[0].get("item_key", "") != item_key:
        notes.append("当前 Issue 的 active exec-plan 与 PR 正文中的 item_key 不一致。")
        return body_context, notes, related_paths

    comparisons = (
        ("issue", "Issue"),
        ("item_key", "item_key"),
        ("item_type", "item_type"),
        ("release", "release"),
        ("sprint", "sprint"),
    )
    mismatched: list[str] = []
    for body_key, metadata_key in comparisons:
        expected = issue_text if body_key == "issue" else body_context[body_key]
        if exec_plan.get(metadata_key, "") != expected:
            mismatched.append(metadata_key)
    if mismatched:
        notes.append(f"PR 正文与 active exec-plan 的字段不一致：{', '.join(mismatched)}。")
        return body_context, notes, related_paths

    merged = dict(body_context)
    merged["exec_plan"] = exec_plan.get("exec_plan", "")
    return merged, notes, related_paths


def build_review_context(meta: dict, worktree_dir: Path) -> dict[str, object]:
    base_ref = meta["baseRefName"]
    raw_sections = parse_all_markdown_sections(str(meta.get("body") or ""))
    sections = parse_markdown_sections(str(meta.get("body") or ""))
    changed_files, diff_stat = fetch_diff_stats(worktree_dir, base_ref)
    item_context, context_notes, related_paths = build_item_context_summary(meta, worktree_dir)
    issue_number = 0
    try:
        issue_number = int(str(item_context.get("issue", "")).strip())
    except ValueError:
        issue_number = 0
    needs_issue_context = bool(issue_number) and not sections.get("issue_summary")
    related_paths.extend(path for path in changed_files if path.startswith("docs/specs/"))
    related_paths.extend(path for path in changed_files if path.startswith("docs/decisions/"))
    related_paths = list(dict.fromkeys(path for path in related_paths if path))

    return {
        "pr_identity": [
            f"- PR: #{meta['number']}",
            f"- 标题: {meta['title']}",
            f"- 链接: {meta['url']}",
            f"- 基线分支: {base_ref}",
            f"- 头部提交: {meta['headRefOid']}",
            f"- 头部分支: {meta.get('headRefName', '')}",
        ],
        "issue_context": fetch_issue_context(issue_number) if needs_issue_context else {"identity": [], "summary": ""},
        "item_context": item_context,
        "raw_sections": raw_sections,
        "pr_sections": sections,
        "changed_files": changed_files,
        "diff_stat": diff_stat,
        "related_paths": related_paths,
        "context_notes": context_notes,
    }


def render_bullet_dict(payload: dict[str, str]) -> list[str]:
    if not payload:
        return ["- 无可确认的结构化事项上下文"]
    return [f"- {key}: {value}" for key, value in payload.items()]


def render_item_context_supplement(section: str) -> str:
    if not section.strip():
        return ""

    redundant_prefixes = (
        "- Issue:",
        "- item_key:",
        "- item_type:",
        "- release:",
        "- sprint:",
    )
    retained = [
        line
        for line in section.splitlines()
        if line.strip() and not any(line.strip().startswith(prefix) for prefix in redundant_prefixes)
    ]
    if not retained:
        return ""
    return "\n".join(retained)


def append_optional_section(lines: list[str], title: str, content: str) -> None:
    content = content.strip()
    if not content:
        return
    lines.extend(["", title, content])


def render_raw_body_fallback(raw_body: str, raw_sections: dict[str, str]) -> str:
    if not raw_body:
        return ""
    if not raw_sections:
        return raw_body

    preamble = raw_sections.get("__preamble__", "").strip()
    extra_headings = [
        heading
        for heading in raw_sections
        if heading not in REVIEW_SECTION_ALIASES and heading not in RAW_BODY_NOISE_HEADINGS
    ]
    if not extra_headings and not preamble:
        return ""

    blocks: list[str] = []
    if preamble:
        blocks.extend([preamble, ""])
    for heading in extra_headings:
        if heading == "__preamble__":
            continue
        content = raw_sections.get(heading, "")
        if not content:
            continue
        blocks.extend([f"## {heading}", content, ""])
    return "\n".join(blocks).strip()


def build_prompt(meta: dict, worktree_dir: Path) -> str:
    base_ref = meta["baseRefName"]
    context = build_review_context(meta, worktree_dir)
    rubric_excerpt = load_reviewer_rubric_excerpt(worktree_dir, base_ref)
    sections = context["pr_sections"]
    raw_body = str(meta.get("body") or "").strip()
    summary_fallback = "无结构化 PR 摘要。"
    raw_body_fallback = render_raw_body_fallback(raw_body, context["raw_sections"])

    lines = [
        "你是 Syvert PR guardian reviewer。",
        f"请在当前工作树中审查 `origin/{base_ref}` 与当前 HEAD 的差异。",
        "优先基于 diff 与必要文件做静态审查，仅在存在明确阻断线索时再运行最小必要命令。",
        "不要运行完整测试套件或与当前变更无关的重型验证。",
        "",
        "执行约束：",
        *[f"- {rule}" for rule in REVIEW_EXECUTION_RULES],
        "",
        "Reviewer Rubric 节选（来自 `code_review.md`）：",
        rubric_excerpt,
        "",
        "PR 基本信息：",
        *context["pr_identity"],
    ]

    issue_summary = sections.get("issue_summary", "").strip()
    item_context_supplement = render_item_context_supplement(sections.get("item_context", ""))
    if context["issue_context"]["identity"] or context["issue_context"]["summary"] or issue_summary:
        lines.extend(
            [
                "",
                "Issue 摘要：",
                *(context["issue_context"]["identity"] or []),
                issue_summary or str(context["issue_context"]["summary"]),
            ]
        )

    lines.extend(
        [
            "",
            "结构化事项上下文：",
            *render_bullet_dict(context["item_context"]),
            "",
            "PR 摘要：",
            sections.get("summary", summary_fallback),
            "",
            "变更文件：",
            format_changed_files(context["changed_files"]),
            "",
            "Diff Stat：",
            str(context["diff_stat"]),
        ]
    )

    append_optional_section(lines, "PR 关联事项补充：", item_context_supplement)
    lines.extend(["", "风险摘要：", sections.get("risk", "未提供结构化风险摘要。")])
    lines.extend(["", "验证摘要：", sections.get("validation", "未提供结构化验证摘要。")])
    lines.extend(["", "回滚摘要：", sections.get("rollback", "未提供结构化回滚摘要。")])
    if context["related_paths"]:
        lines.extend(["", "相关工件路径：", *[f"- `{path}`" for path in context["related_paths"]]])
    else:
        lines.extend(["", "相关工件路径：", "- 未直接定位到相关 spec / exec-plan / decision 工件。"])
    if context["context_notes"]:
        lines.extend(["", "Context Notes：", *[f"- {note}" for note in context["context_notes"]]])

    if raw_body_fallback:
        lines.extend(["", "PR 正文 fallback：", raw_body_fallback])

    return "\n".join(lines).rstrip() + "\n"


def run_codex_review(worktree_dir: Path, prompt: str, result_path: Path) -> dict:
    scratch_dir = worktree_dir / ".codex-tmp"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    scratch_dir_text = str(scratch_dir)
    env["TMPDIR"] = scratch_dir_text
    env["TMP"] = scratch_dir_text
    env["TEMP"] = scratch_dir_text
    timeout_seconds = codex_review_timeout_seconds()
    try:
        completed = subprocess.run(
            [
                "codex",
                "exec",
                "-C",
                str(worktree_dir),
                "-s",
                "workspace-write",
                "--output-schema",
                str(SCHEMA_PATH),
                "-o",
                str(result_path),
                "-",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        timeout_hint = exc.timeout if exc.timeout is not None else timeout_seconds
        raise SystemExit(f"Codex 审查超时（>{timeout_hint} 秒），未产出 guardian verdict。") from exc
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or "Codex 审查失败。")
    if result_path.exists():
        return json.loads(result_path.read_text(encoding="utf-8"))
    if completed.stdout.strip():
        return json.loads(completed.stdout)
    raise SystemExit("Codex 审查未产出结构化结果。")


def severity_label(severity: str) -> str:
    mapping = {
        "critical": "P0 / critical",
        "high": "P1 / high",
        "medium": "P2 / medium",
        "low": "P3 / low",
    }
    return mapping.get(severity, severity)


def build_review_markdown(result: dict) -> str:
    lines = [
        "## PR Review 结论",
        "",
        f"**结论**: {result['verdict']}",
        "",
        f"**允许合并**: {bool_text(result['safe_to_merge'])}",
        "",
        f"**摘要**: {result['summary']}",
        "",
        "### 需要关注的问题",
        "",
    ]

    findings = result.get("findings", [])
    if not findings:
        lines.append("- 未发现新的阻断性问题。")
    else:
        for index, finding in enumerate(findings, start=1):
            location = finding["code_location"]
            line_range = location["line_range"]
            lines.extend(
                [
                    f"{index}. **[{severity_label(finding['severity'])}] {finding['title']}**",
                    f"文件: `{location['absolute_file_path']}` (L{line_range['start']}-L{line_range['end']})",
                    f"说明: {finding['details']}",
                    "",
                ]
            )

    lines.extend(["### 合并前动作", ""])
    actions = result.get("required_actions", [])
    if not actions:
        lines.append("- 无。")
    else:
        lines.extend([f"- {action}" for action in actions])
    return "\n".join(lines).rstrip() + "\n"


def post_review(pr_number: int, meta: dict, result: dict) -> None:
    reviewer = run(["gh", "api", "user", "--jq", ".login"], cwd=REPO_ROOT).stdout.strip()
    author = (meta.get("author") or {}).get("login", "")
    markdown = build_review_markdown(result)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(markdown)
        body_file = Path(handle.name)

    try:
        if reviewer == author:
            run(["gh", "pr", "review", str(pr_number), "--comment", "--body-file", str(body_file)], cwd=REPO_ROOT)
            return

        action = "--approve" if result["verdict"] == "APPROVE" else "--request-changes"
        run(["gh", "pr", "review", str(pr_number), action, "--body-file", str(body_file)], cwd=REPO_ROOT)
    finally:
        if body_file.exists():
            os.unlink(body_file)


def all_checks_pass(pr_number: int) -> bool:
    completed = run(
        ["gh", "pr", "checks", str(pr_number), "--json", "name,bucket,state,link"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or "无法读取 GitHub checks。")
    checks = json.loads(completed.stdout or "[]")
    if not checks:
        return False
    return all(item.get("bucket") == "pass" for item in checks)


def review_once(pr_number: int, *, post: bool, json_output: str | None) -> tuple[dict, dict]:
    require_auth()
    meta = pr_meta(pr_number)
    temp_dir, worktree_dir = prepare_worktree(pr_number, meta)
    try:
        result_path = temp_dir / "review.json"
        result = run_codex_review(worktree_dir, build_prompt(meta, worktree_dir), result_path)
        payload = build_guardian_payload(meta, result)
        save_guardian_result(pr_number, payload)
        markdown = build_review_markdown(result)
        if json_output:
            Path(json_output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if post:
            post_review(pr_number, meta, result)
        print(markdown)
        return meta, result
    finally:
        cleanup(temp_dir)


def merge_if_safe(pr_number: int, *, post: bool, delete_branch: bool, refresh_review: bool) -> int:
    require_auth()
    current = pr_meta(pr_number)
    payload = None if refresh_review else find_latest_guardian_result(pr_number, current["headRefOid"])

    if payload:
        print(f"复用已有 guardian verdict: {payload['verdict']} @ {payload['head_sha']}")
        result = {
            "verdict": payload["verdict"],
            "safe_to_merge": payload["safe_to_merge"],
            "summary": payload.get("summary", ""),
        }
        reviewed_head_sha = payload["head_sha"]
    else:
        meta, result = review_once(pr_number, post=post, json_output=None)
        reviewed_head_sha = meta["headRefOid"]
        current = pr_meta(pr_number)

    if result["verdict"] != "APPROVE":
        raise SystemExit("guardian 未给出 APPROVE，拒绝合并。")
    if not result["safe_to_merge"]:
        raise SystemExit("guardian 认为当前 PR 不安全，拒绝合并。")

    if current["isDraft"]:
        raise SystemExit("PR 仍为 Draft，拒绝合并。")
    if current["headRefOid"] != reviewed_head_sha:
        raise SystemExit("审查后 PR HEAD 已变化，拒绝合并。")
    if not all_checks_pass(pr_number):
        raise SystemExit("GitHub checks 未全部通过，拒绝合并。")

    command = [
        "gh",
        "pr",
        "merge",
        str(pr_number),
        "--squash",
        "--match-head-commit",
        current["headRefOid"],
    ]
    if delete_branch:
        command.append("--delete-branch")
    run(command, cwd=REPO_ROOT)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "review":
        review_once(args.pr_number, post=args.post_review, json_output=args.json_output)
        return 0
    return merge_if_safe(
        args.pr_number,
        post=args.post_review,
        delete_branch=args.delete_branch,
        refresh_review=args.refresh_review,
    )


if __name__ == "__main__":
    raise SystemExit(main())
