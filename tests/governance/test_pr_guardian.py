from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from scripts.pr_guardian import (
    build_item_context_summary,
    build_prompt,
    build_review_context,
    extract_reviewer_rubric_excerpt,
    find_latest_guardian_result,
    load_guardian_state,
    merge_if_safe,
    review_once,
    run_codex_review,
    save_guardian_result,
)


class GuardianStateTests(unittest.TestCase):
    def test_load_guardian_state_falls_back_to_legacy_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_new = Path(temp_dir) / "missing-guardian.json"
            legacy_path = Path(temp_dir) / "syvert-pr-guardian-results.json"
            legacy_path.write_text('{"prs":{"1":{"verdict":"APPROVE"}}}', encoding="utf-8")

            with patch("scripts.pr_guardian.DEFAULT_STATE_FILE", missing_new):
                with patch("scripts.pr_guardian.guardian_legacy_state_path", return_value=legacy_path):
                    payload = load_guardian_state(missing_new)

            self.assertIn("prs", payload)
            self.assertIn("1", payload["prs"])

    def test_find_latest_guardian_result_uses_local_state_for_matching_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "guardian.json"
            save_guardian_result(
                1,
                {
                    "schema_version": 1,
                    "pr_number": 1,
                    "head_sha": "sha-1",
                    "verdict": "APPROVE",
                    "safe_to_merge": True,
                    "summary": "cached",
                    "reviewed_at": "2026-03-28T10:00:00Z",
                },
                path=state_path,
            )

            payload = find_latest_guardian_result(1, "sha-1", path=state_path)

            self.assertIsNotNone(payload)
            self.assertEqual(payload["head_sha"], "sha-1")

    def test_find_latest_guardian_result_rejects_stale_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "guardian.json"
            save_guardian_result(
                1,
                {
                    "schema_version": 1,
                    "pr_number": 1,
                    "head_sha": "sha-1",
                    "verdict": "APPROVE",
                    "safe_to_merge": True,
                    "summary": "cached",
                    "reviewed_at": "2026-03-28T10:00:00Z",
                },
                path=state_path,
            )

            payload = find_latest_guardian_result(1, "sha-2", path=state_path)

            self.assertIsNone(payload)


class CodexReviewExecutionTests(unittest.TestCase):
    @patch("scripts.pr_guardian.subprocess.run")
    def test_run_codex_review_falls_back_to_stdout_json(self, subprocess_run_mock) -> None:
        subprocess_run_mock.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"verdict":"APPROVE","safe_to_merge":true,"summary":"ok","findings":[],"required_actions":[]}',
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_codex_review(Path(temp_dir), "prompt", Path(temp_dir) / "review.json")

        self.assertEqual(result["verdict"], "APPROVE")
        self.assertTrue(result["safe_to_merge"])
        command = subprocess_run_mock.call_args.args[0]
        self.assertIn("workspace-write", command)
        env = subprocess_run_mock.call_args.kwargs["env"]
        self.assertTrue(env["TMPDIR"].endswith(".codex-tmp"))

    @patch("scripts.pr_guardian.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["codex"], timeout=300))
    def test_run_codex_review_times_out_with_actionable_error(self, subprocess_run_mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(SystemExit) as ctx:
                run_codex_review(Path(temp_dir), "prompt", Path(temp_dir) / "review.json")

        self.assertIn("Codex 审查超时", str(ctx.exception))
        subprocess_run_mock.assert_called_once()

    def test_find_latest_guardian_result_rejects_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "guardian.json"
            save_guardian_result(
                1,
                {
                    "schema_version": 1,
                    "pr_number": 1,
                    "head_sha": "sha-1",
                    "verdict": "MAYBE",
                    "safe_to_merge": True,
                    "summary": "cached",
                    "reviewed_at": "2026-03-28T10:00:00Z",
                },
                path=state_path,
            )

            payload = find_latest_guardian_result(1, "sha-1", path=state_path)

            self.assertIsNone(payload)

    def test_build_prompt_prefers_structured_context_and_omits_merge_gate_doc_text(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: 精简 guardian review context",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "## 摘要\n\n- 变更目的：精简 prompt\n",
        }

        with patch(
            "scripts.pr_guardian.build_review_context",
            return_value={
                "pr_identity": ["- PR: #24", "- 标题: 治理: 精简 guardian review context"],
                "issue_context": {
                    "identity": ["- Issue: #24", "- 标题: governance: lean guardian review context"],
                    "summary": "## Goal\n\n- 精简 review context",
                },
                "item_context": {"issue": "24", "item_key": "GOV-0024-guardian-review-context"},
                "raw_sections": {
                    "摘要": "- 变更目的：精简 prompt",
                    "关联事项": "- Issue: #24\n- Closing: Fixes #24",
                    "风险级别": "- `medium`",
                    "验证": "- python3 -m unittest",
                    "回滚": "- revert PR",
                    "检查清单": "- [x] 已填写 Closing",
                },
                "pr_sections": {
                    "item_context": "- Issue: #24\n- Closing: Fixes #24",
                    "summary": "- 变更目的：精简 prompt",
                    "risk": "- `medium`",
                    "validation": "- python3 -m unittest",
                    "rollback": "- revert PR",
                    "checklist": "- [x] 已填写 Closing",
                },
                "checks": ["- governance: bucket=pass, state=SUCCESS"],
                "worktree_binding": [{"key": "issue-24", "path": "/tmp/issue-24"}],
                "changed_files": ["scripts/pr_guardian.py", "tests/governance/test_pr_guardian.py"],
                "diff_stat": "2 files changed, 42 insertions(+), 8 deletions(-)",
                "related_paths": ["docs/exec-plans/GOV-0024-guardian-review-context.md"],
                "context_notes": ["结构化事项上下文已加载。"],
            },
        ):
            with patch("scripts.pr_guardian.load_reviewer_rubric_excerpt", return_value="## Review Rubric\n- contract 一致性"):
                prompt = build_prompt(meta, Path("/tmp/worktree"))

        self.assertIn("结构化事项上下文：", prompt)
        self.assertIn("Issue 摘要：", prompt)
        self.assertIn("## Goal", prompt)
        self.assertIn("GOV-0024-guardian-review-context", prompt)
        self.assertIn("Fixes #24", prompt)
        self.assertIn("检查清单：", prompt)
        self.assertIn("Diff Stat：", prompt)
        self.assertIn("docs/exec-plans/GOV-0024-guardian-review-context.md", prompt)
        self.assertIn("## Review Rubric", prompt)
        self.assertNotIn("PR 正文 fallback：", prompt)
        self.assertNotIn("进入 `merge-ready` 前，必须同时满足", prompt)
        self.assertNotIn("默认 Squash Merge", prompt)

    def test_build_prompt_uses_raw_body_only_when_structured_sections_are_incomplete(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: 精简 guardian review context",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "## 摘要\n\n- 变更目的：精简 prompt\n\n## 验证\n\n- 已执行：单测\n\n## 自定义说明\n\n- 保留给 reviewer 的补充信息\n",
        }

        with patch(
            "scripts.pr_guardian.build_review_context",
            return_value={
                "pr_identity": ["- PR: #24"],
                "issue_context": {"identity": ["- Issue: #24"], "summary": "## Goal\n- 精简"},
                "item_context": {"issue": "24"},
                "raw_sections": {
                    "摘要": "- 变更目的：精简 prompt",
                    "验证": "- 已执行：单测",
                    "自定义说明": "- 保留给 reviewer 的补充信息",
                },
                "pr_sections": {
                    "summary": "- 变更目的：精简 prompt",
                    "validation": "- 已执行：单测",
                },
                "changed_files": ["scripts/pr_guardian.py"],
                "diff_stat": "1 file changed",
                "related_paths": [],
                "context_notes": [],
            },
        ):
            with patch("scripts.pr_guardian.load_reviewer_rubric_excerpt", return_value="## Review Rubric\n- contract 一致性"):
                prompt = build_prompt(meta, Path("/tmp/worktree"))

        self.assertIn("PR 正文 fallback：", prompt)
        self.assertIn("## 自定义说明", prompt)

    def test_build_item_context_summary_returns_exec_plan_and_related_paths(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## 关联事项",
                    "",
                    "- Issue: #24",
                    "- item_key: `GOV-0024-guardian-review-context`",
                    "- item_type: `GOV`",
                    "- release: `v0.1.0`",
                    "- sprint: `2026-S14`",
                ]
            )
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            exec_plan_path = repo_root / "docs" / "exec-plans" / "GOV-0024-guardian-review-context.md"
            exec_plan_path.parent.mkdir(parents=True, exist_ok=True)
            exec_plan_path.write_text(
                "\n".join(
                    [
                        "# GOV-0024 执行计划",
                        "",
                        "## 关联信息",
                        "",
                        "- item_key：`GOV-0024-guardian-review-context`",
                        "- Issue：`#24`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "- 关联 spec：无（治理脚本事项）",
                        "- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`",
                        "- active 收口事项：`GOV-0024-guardian-review-context`",
                    ]
                ),
                encoding="utf-8",
            )

            with patch("scripts.pr_guardian.REPO_ROOT", repo_root):
                with patch(
                    "scripts.pr_guardian.load_item_context_from_exec_plan",
                    return_value={
                        "Issue": "24",
                        "item_key": "GOV-0024-guardian-review-context",
                        "item_type": "GOV",
                        "release": "v0.1.0",
                        "sprint": "2026-S14",
                        "exec_plan": "docs/exec-plans/GOV-0024-guardian-review-context.md",
                    },
                ):
                    with patch(
                        "scripts.pr_guardian.active_exec_plans_for_issue",
                        return_value=[{"item_key": "GOV-0024-guardian-review-context"}],
                    ):
                        payload, notes, related_paths = build_item_context_summary(meta, repo_root)

        self.assertEqual(payload["exec_plan"], "docs/exec-plans/GOV-0024-guardian-review-context.md")
        self.assertEqual(notes, [])
        self.assertIn("docs/decisions/ADR-0001-governance-bootstrap-contract.md", related_paths)
        self.assertNotIn("无（治理脚本事项）", related_paths)

    def test_build_review_context_uses_pr_worktree_as_repo_root(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: 精简 guardian review context",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "",
        }
        worktree_dir = Path("/tmp/pr-worktree")

        with patch("scripts.pr_guardian.fetch_diff_stats", return_value=(["scripts/pr_guardian.py"], "1 file changed")):
            with patch(
                "scripts.pr_guardian.build_item_context_summary",
                return_value=({"issue": "24", "item_key": "GOV-0024-guardian-review-context"}, [], []),
            ) as build_item_context_summary_mock:
                with patch(
                    "scripts.pr_guardian.fetch_issue_context",
                    return_value={"identity": ["- Issue: #24"], "summary": "## Goal\n- 精简"},
                ) as fetch_issue_context_mock:
                    payload = build_review_context(meta, worktree_dir)

        build_item_context_summary_mock.assert_called_once_with(meta, worktree_dir)
        fetch_issue_context_mock.assert_called_once_with(24)
        self.assertEqual(payload["item_context"]["item_key"], "GOV-0024-guardian-review-context")

    def test_extract_reviewer_rubric_excerpt_excludes_merge_gate_sections(self) -> None:
        excerpt = extract_reviewer_rubric_excerpt(
            "\n".join(
                [
                    "# 审查标准",
                    "",
                    "## 工件完整性检查",
                    "",
                    "- 输入必须完整",
                    "",
                    "## Review Rubric",
                    "",
                    "- 关注 contract 与回归风险",
                    "",
                    "## 合并门禁",
                    "",
                    "- 不应出现在 reviewer excerpt",
                    "",
                    "## 职责边界说明",
                    "",
                    "- reviewer 与 guardian 分层",
                ]
            )
        )

        self.assertIn("## 工件完整性检查", excerpt)
        self.assertIn("## Review Rubric", excerpt)
        self.assertIn("## 职责边界说明", excerpt)
        self.assertNotIn("## 合并门禁", excerpt)

    @patch("scripts.pr_guardian.cleanup")
    @patch("scripts.pr_guardian.run_codex_review")
    @patch("scripts.pr_guardian.build_prompt", return_value="lean prompt")
    @patch("scripts.pr_guardian.prepare_worktree")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    def test_review_once_builds_prompt_from_worktree_context(
        self,
        require_auth_mock,
        pr_meta_mock,
        prepare_worktree_mock,
        build_prompt_mock,
        run_codex_review_mock,
        cleanup_mock,
    ) -> None:
        temp_dir = Path("/tmp/guardian-temp")
        worktree_dir = Path("/tmp/guardian-temp/worktree")
        pr_meta_mock.return_value = {
            "number": 24,
            "title": "治理: 精简 guardian review context",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "",
        }
        prepare_worktree_mock.return_value = (temp_dir, worktree_dir)
        run_codex_review_mock.return_value = {
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "ok",
            "findings": [],
            "required_actions": [],
        }

        review_once(24, post=False, json_output=None)

        build_prompt_mock.assert_called_once_with(pr_meta_mock.return_value, worktree_dir)
        run_codex_review_mock.assert_called_once_with(worktree_dir, "lean prompt", temp_dir / "review.json")
        cleanup_mock.assert_called_once_with(temp_dir)


class MergeIfSafeTests(unittest.TestCase):
    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_cached_request_changes(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-request-changes",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-request-changes",
            "verdict": "REQUEST_CHANGES",
            "safe_to_merge": False,
            "summary": "blocked",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("guardian 未给出 APPROVE", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_cached_safe_to_merge_false(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-safe-false",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-safe-false",
            "verdict": "APPROVE",
            "safe_to_merge": False,
            "summary": "blocked",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("guardian 认为当前 PR 不安全", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_reuses_existing_guardian_result(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-1",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-1",
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "cached",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        exit_code = merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertEqual(exit_code, 0)
        review_once_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)
        run_mock.assert_called_once_with(
            ["gh", "pr", "merge", "1", "--squash", "--match-head-commit", "sha-1"],
            cwd=ANY,
        )

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result", return_value=None)
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_runs_review_when_no_cached_result(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-2",
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-2",
            },
        ]
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-2",
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh",
            },
        )
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        exit_code = merge_if_safe(1, post=False, delete_branch=True, refresh_review=False)

        self.assertEqual(exit_code, 0)
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)
        run_mock.assert_called_once_with(
            ["gh", "pr", "merge", "1", "--squash", "--match-head-commit", "sha-2", "--delete-branch"],
            cwd=ANY,
        )

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_refresh_review_ignores_cached_result(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-3",
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-3",
            },
        ]
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-3",
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "refreshed",
            },
        )
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        exit_code = merge_if_safe(1, post=False, delete_branch=False, refresh_review=True)

        self.assertEqual(exit_code, 0)
        find_result_mock.assert_not_called()
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_when_head_changes_after_cached_review(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-current",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-reviewed",
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "cached",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("审查后 PR HEAD 已变化", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_not_called()

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=False)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_when_checks_not_green_after_cached_review(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-green-check",
        }
        find_result_mock.return_value = {
            "schema_version": 1,
            "pr_number": 1,
            "head_sha": "sha-green-check",
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "cached",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("GitHub checks 未全部通过", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
