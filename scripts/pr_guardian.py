#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.common import REPO_ROOT, bool_text, dump_json, ensure_parent, load_json, require_cli, run


SCHEMA_PATH = REPO_ROOT / "scripts" / "policy" / "pr_review_result_schema.json"
PROMPT_PATH = REPO_ROOT / "code_review.md"
DEFAULT_STATE_FILE = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "state" / "syvert-pr-guardian-results.json"
VALID_VERDICTS = {"APPROVE", "REQUEST_CHANGES"}


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
    if not path.exists():
        return {"prs": {}}
    return load_json(path)


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


def build_prompt(meta: dict) -> str:
    base_ref = meta["baseRefName"]
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    return (
        f"{prompt}\n\n"
        "PR 元数据：\n"
        f"- PR: #{meta['number']}\n"
        f"- 标题: {meta['title']}\n"
        f"- 链接: {meta['url']}\n"
        f"- 基线分支: {base_ref}\n"
        f"- 头部提交: {meta['headRefOid']}\n"
        f"- PR 描述:\n{meta.get('body') or ''}\n\n"
        f"请在当前工作树中审查 `origin/{base_ref}` 与当前 HEAD 的差异。\n"
    )


def run_codex_review(worktree_dir: Path, prompt: str, result_path: Path) -> dict:
    completed = subprocess.run(
        [
            "codex",
            "exec",
            "-C",
            str(worktree_dir),
            "-s",
            "read-only",
            "--output-schema",
            str(SCHEMA_PATH),
            "-o",
            str(result_path),
            "-",
        ],
        cwd=str(REPO_ROOT),
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or "Codex 审查失败。")
    return json.loads(result_path.read_text(encoding="utf-8"))


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
        result = run_codex_review(worktree_dir, build_prompt(meta), result_path)
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
