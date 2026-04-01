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
from scripts.state_paths import guardian_legacy_state_path, guardian_state_path, worktrees_state_path


SCHEMA_PATH = REPO_ROOT / "scripts" / "policy" / "pr_review_result_schema.json"
DEFAULT_STATE_FILE = guardian_state_path()
VALID_VERDICTS = {"APPROVE", "REQUEST_CHANGES"}
CODEX_REVIEW_TIMEOUT_SECONDS = int(os.environ.get("SYVERT_GUARDIAN_TIMEOUT_SECONDS", "300"))
REVIEW_REQUIRED_BODY_FIELDS = ("issue", "item_key", "item_type", "release", "sprint")
REVIEW_RULES = (
    "工件完整性只用于确认输入是否足够，不要把 checks、Draft 状态或 merge 动作当成 reviewer 结论来源。",
    "优先按 reviewer rubric 判断 contract 一致性、行为正确性、回归风险、测试有效性、错误处理、架构边界、可维护性、可观测性、安全/性能/成本、发布与回滚准备。",
    "若缺少必要工件或验证证据，应明确指出阻断项；merge gate、head 绑定与 squash merge 安全性由 guardian gate 入口单独消费。",
)
REVIEW_SECTION_ALIASES = {
    "摘要": "summary",
    "关联事项": "item_context",
    "风险级别": "risk",
    "变更文件": "changed_files",
    "验证": "validation",
    "回滚": "rollback",
}


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


def parse_markdown_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            current_key = REVIEW_SECTION_ALIASES.get(heading)
            if current_key:
                sections.setdefault(current_key, [])
            continue
        if current_key:
            sections[current_key].append(line.rstrip())

    return {key: "\n".join(value).strip() for key, value in sections.items() if "\n".join(value).strip()}


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


def fetch_checks_summary(pr_number: int) -> list[str]:
    completed = run(
        ["gh", "pr", "checks", str(pr_number), "--json", "name,bucket,state"],
        cwd=REPO_ROOT,
        check=False,
    )
    if completed.returncode != 0:
        return ["- checks 状态暂不可用"]
    payload = json.loads(completed.stdout or "[]")
    if not payload:
        return ["- 暂无 checks 结果"]
    return [
        f"- {item.get('name', 'unknown')}: bucket={item.get('bucket', '')}, state={item.get('state', '')}"
        for item in payload
    ]


def load_worktree_binding(branch: str, *, path: Path = worktrees_state_path()) -> tuple[list[dict], str | None]:
    if not path.exists():
        return [], "worktree 状态文件缺失。"
    state = load_json(path)
    matches = [item for item in (state.get("worktrees") or {}).values() if item.get("branch") == branch]
    if not matches:
        return [], "未找到当前分支的 worktree 绑定。"
    if len(matches) > 1:
        return matches, "当前分支命中多个 worktree 绑定。"
    return matches, None


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
            if value and value != "无":
                links.append(value)
    return links


def build_item_context_summary(meta: dict) -> tuple[dict[str, str], list[str], list[str]]:
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
    exec_plan = load_item_context_from_exec_plan(REPO_ROOT, item_key)
    if exec_plan.get("conflict") == "duplicate_metadata_keys":
        notes.append("active exec-plan 元数据存在重复键，无法确认唯一事项上下文。")
        return body_context, notes, related_paths
    if exec_plan.get("conflict") == "multiple_active_exec_plans":
        notes.append("当前 item_key 命中多个 active exec-plan。")
        return body_context, notes, related_paths
    if not exec_plan:
        notes.append("当前 item_key 未找到 active exec-plan。")
        return body_context, notes, related_paths

    issue_exec_plans = active_exec_plans_for_issue(REPO_ROOT, issue_number)
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
    if merged["exec_plan"]:
        related_paths.extend(extract_related_links_from_exec_plan(REPO_ROOT / merged["exec_plan"]))
    return merged, notes, related_paths


def build_review_context(meta: dict, worktree_dir: Path) -> dict[str, object]:
    base_ref = meta["baseRefName"]
    sections = parse_markdown_sections(str(meta.get("body") or ""))
    changed_files, diff_stat = fetch_diff_stats(worktree_dir, base_ref)
    item_context, context_notes, related_paths = build_item_context_summary(meta)
    worktree_matches, worktree_note = load_worktree_binding(meta.get("headRefName", ""))
    if worktree_note:
        context_notes.append(worktree_note)

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
        "item_context": item_context,
        "pr_sections": sections,
        "checks": fetch_checks_summary(meta["number"]),
        "worktree_binding": worktree_matches,
        "changed_files": changed_files,
        "diff_stat": diff_stat,
        "related_paths": related_paths,
        "context_notes": context_notes,
    }


def render_bullet_dict(payload: dict[str, str]) -> list[str]:
    if not payload:
        return ["- 无可确认的结构化事项上下文"]
    return [f"- {key}: {value}" for key, value in payload.items()]


def render_worktree_binding(matches: list[dict]) -> list[str]:
    if not matches:
        return ["- 无可确认的 worktree 绑定"]
    return [f"- {item.get('key', '')}: {item.get('path', '')}" for item in matches]


def build_prompt(meta: dict, worktree_dir: Path) -> str:
    base_ref = meta["baseRefName"]
    context = build_review_context(meta, worktree_dir)
    sections = context["pr_sections"]
    raw_body = str(meta.get("body") or "").strip()
    summary_fallback = raw_body if raw_body else "无 PR 正文。"

    lines = [
        "你是 Syvert PR guardian reviewer。",
        f"请在当前工作树中审查 `origin/{base_ref}` 与当前 HEAD 的差异。",
        "优先基于 diff 与必要文件做静态审查，仅在存在明确阻断线索时再运行最小必要命令。",
        "不要运行完整测试套件或与当前变更无关的重型验证。",
        "",
        "最小关键规则：",
        *[f"- {rule}" for rule in REVIEW_RULES],
        "",
        "PR 基本信息：",
        *context["pr_identity"],
        "",
        "结构化事项上下文：",
        *render_bullet_dict(context["item_context"]),
        "",
        "PR 摘要：",
        sections.get("summary", summary_fallback),
        "",
        "风险摘要：",
        sections.get("risk", "无结构化风险摘要。"),
        "",
        "验证摘要：",
        sections.get("validation", "无结构化验证摘要。"),
        "",
        "回滚摘要：",
        sections.get("rollback", "无结构化回滚摘要。"),
        "",
        "变更文件：",
        format_changed_files(context["changed_files"]),
        "",
        "Diff Stat：",
        str(context["diff_stat"]),
        "",
        "相关工件路径：",
        *([f"- `{path}`" for path in context["related_paths"]] or ["- 无直接定位到的 spec / exec-plan / decision 工件"]),
        "",
        "Checks 摘要：",
        *context["checks"],
        "",
        "Worktree 绑定：",
        *render_worktree_binding(context["worktree_binding"]),
        "",
        "Context Notes：",
        *([f"- {note}" for note in context["context_notes"]] or ["- 无"]),
    ]

    if not sections and raw_body:
        lines.extend(["", "PR 正文 fallback：", raw_body])

    return "\n".join(lines).rstrip() + "\n"


def run_codex_review(worktree_dir: Path, prompt: str, result_path: Path) -> dict:
    scratch_dir = worktree_dir / ".codex-tmp"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    scratch_dir_text = str(scratch_dir)
    env["TMPDIR"] = scratch_dir_text
    env["TMP"] = scratch_dir_text
    env["TEMP"] = scratch_dir_text
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
            timeout=CODEX_REVIEW_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"Codex 审查超时（>{CODEX_REVIEW_TIMEOUT_SECONDS} 秒），未产出 guardian verdict。") from exc
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
