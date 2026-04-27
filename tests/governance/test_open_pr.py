from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from unittest.mock import ANY, patch

from scripts.common import CommandError, default_github_repo, normalize_integration_ref_for_comparison, parse_github_repo_from_remote_url
from scripts.open_pr import (
    build_body,
    build_issue_summary,
    governing_artifact_label,
    extract_issue_canonical_integration_fields,
    extract_issue_summary_sections,
    has_formal_spec_core_file_changes,
    parse_args,
    validate_current_worktree_binding,
    validate_integration_args,
    validate_pr_preflight,
)


def write_exec_plan(
    repo: Path,
    *,
    item_key: str = "GOV-0015-item-context-gate",
    issue: str = "#19",
    item_type: str = "GOV",
    release: str = "v0.1.0",
    sprint: str = "2026-S14",
    active_item_key: str = "GOV-0015-item-context-gate",
    related_spec: str | None = None,
    related_decision: str | None = None,
) -> None:
    exec_plans = repo / "docs" / "exec-plans"
    exec_plans.mkdir(parents=True, exist_ok=True)
    (exec_plans / f"{item_key}.md").write_text(
        "\n".join(
            [
                "# plan",
                "",
                "## 关联信息",
                "",
                f"- item_key：`{item_key}`",
                f"- Issue：`{issue}`",
                f"- item_type：`{item_type}`",
                f"- release：`{release}`",
                f"- sprint：`{sprint}`",
                *( [f"- 关联 spec：`{related_spec}`"] if related_spec else [] ),
                *( [f"- 关联 decision：`{related_decision}`"] if related_decision else [] ),
                f"- active 收口事项：`{active_item_key}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_formal_spec_suite(
    repo: Path,
    *,
    suite_name: str = "FR-0001-governance-stack-v1",
    with_todo: bool = False,
) -> None:
    fr_dir = repo / "docs" / "specs" / suite_name
    fr_dir.mkdir(parents=True, exist_ok=True)
    (fr_dir / "spec.md").write_text(
        "\n".join(
            [
                "# spec",
                "",
                "## GWT 验收场景",
                "",
                "Given x",
                "When y",
                "Then z",
                "",
                "## 异常与边界场景",
                "",
                "- x",
                "",
                "## 验收标准",
                "",
                "- [ ] x",
            ]
        ),
        encoding="utf-8",
    )
    (fr_dir / "plan.md").write_text(
        "\n".join(
            [
                "# plan",
                "",
                "## 实施目标",
                "",
                "- x",
                "",
                "## 分阶段拆分",
                "",
                "- x",
                "",
                "## 实现约束",
                "",
                "- x",
                "",
                "## 测试与验证策略",
                "",
                "- x",
                "",
                "## TDD 范围",
                "",
                "- x",
                "",
                "## 并行 / 串行关系",
                "",
                "- x",
                "",
                "## 进入实现前条件",
                "",
                "- [ ] x",
            ]
        ),
        encoding="utf-8",
    )
    if with_todo:
        (fr_dir / "TODO.md").write_text("# todo\n", encoding="utf-8")


def write_decision(repo: Path, path: str, *, issue: str, item_key: str) -> None:
    decision_path = repo / path
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        "\n".join(
            [
                "# ADR",
                "",
                f"- Issue：`{issue}`",
                f"- item_key：`{item_key}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


class OpenPrPreflightTests(unittest.TestCase):
    def test_parse_github_repo_from_remote_url_supports_https_and_ssh(self) -> None:
        self.assertEqual(
            parse_github_repo_from_remote_url("https://github.com/MC-and-his-Agents/Syvert.git"),
            "MC-and-his-Agents/Syvert",
        )
        self.assertEqual(
            parse_github_repo_from_remote_url("git@github.com:MC-and-his-Agents/Syvert.git"),
            "MC-and-his-Agents/Syvert",
        )
        self.assertEqual(
            parse_github_repo_from_remote_url("ssh://git@github.com/MC-and-his-Agents/Syvert.git"),
            "MC-and-his-Agents/Syvert",
        )

    @patch("scripts.common.default_github_repo", return_value="MC-and-his-Agents/Syvert")
    def test_normalize_integration_ref_for_comparison_resolves_local_issue_against_repo_slug(self, default_repo_mock) -> None:
        normalized = normalize_integration_ref_for_comparison("#12")

        self.assertEqual(normalized, "issue:mc-and-his-agents/syvert#12")
        default_repo_mock.assert_called_once_with()

    @patch("scripts.common.run")
    def test_default_github_repo_ignores_env_and_remote_drift_without_explicit_override(self, run_mock) -> None:
        default_github_repo.cache_clear()
        try:
            with patch.dict(
                "scripts.common.os.environ",
                {"GITHUB_REPOSITORY": "fork-owner/Syvert", "SYVERT_GITHUB_REPO": ""},
                clear=True,
            ):
                run_mock.return_value = subprocess.CompletedProcess(
                    args=["git", "config", "--get", "remote.origin.url"],
                    returncode=0,
                    stdout="git@github.com:MC-and-his-Agents/WebEnvoy.git\n",
                    stderr="",
                )
                self.assertEqual(default_github_repo(), "MC-and-his-Agents/Syvert")
        finally:
            default_github_repo.cache_clear()

        run_mock.assert_not_called()

    def test_default_github_repo_accepts_explicit_syvert_override(self) -> None:
        default_github_repo.cache_clear()
        try:
            with patch.dict(
                "scripts.common.os.environ",
                {"SYVERT_GITHUB_REPO": "MC-and-his-Agents/Syvert-Shadow"},
                clear=True,
            ):
                self.assertEqual(default_github_repo(), "MC-and-his-Agents/Syvert-Shadow")
        finally:
            default_github_repo.cache_clear()

    def test_normalize_integration_ref_for_comparison_normalizes_project_item_variants(self) -> None:
        with_view = "https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test"
        reordered_query = "https://github.com/orgs/MC-and-his-Agents/projects/3?itemId=PVTI_test&pane=issue"

        self.assertEqual(
            normalize_integration_ref_for_comparison(with_view),
            "project-item:mc-and-his-agents/3#PVTI_test",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison(with_view),
            normalize_integration_ref_for_comparison(reordered_query),
        )

    def test_validate_integration_args_rejects_empty_ref_for_gated_pr(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "active",
                "--integration-ref",
                "",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertTrue(any("`integration_ref` 不能为空" in error for error in errors))

    def test_validate_integration_args_requires_gate_for_shared_contract_surface(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "none",
                "--integration-ref",
                "none",
                "--external-dependency",
                "none",
                "--merge-gate",
                "local_only",
                "--contract-surface",
                "errors",
            ]
        )

        errors = validate_integration_args(args)

        self.assertTrue(any("`merge_gate` 必须为 `integration_check_required`" in error for error in errors))
        self.assertTrue(any("`integration_touchpoint` 不能为 `none`" in error for error in errors))

    def test_validate_integration_args_requires_gate_for_shared_contract_change(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "none",
                "--shared-contract-changed",
                "yes",
                "--integration-ref",
                "none",
                "--external-dependency",
                "none",
                "--merge-gate",
                "local_only",
                "--contract-surface",
                "none",
            ]
        )

        errors = validate_integration_args(args)

        self.assertTrue(any("共享契约" in error and "`integration_check_required`" in error for error in errors))

    def test_validate_integration_args_rejects_dependency_with_none_touchpoint(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "none",
                "--integration-ref",
                "https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "none",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertTrue(any("`integration_touchpoint` 不能为 `none`" in error for error in errors))

    def test_validate_integration_args_requires_touchpoint_for_gated_pr(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "none",
                "--integration-ref",
                "https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "--external-dependency",
                "none",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "none",
                "--joint-acceptance-needed",
                "no",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertTrue(
            any("`merge_gate=integration_check_required` 时，`integration_touchpoint` 不能为 `none`" in error for error in errors)
        )

    def test_validate_integration_args_rejects_uncheckable_integration_ref(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "active",
                "--integration-ref",
                "later",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertTrue(any("可核查的具体 integration issue / item" in error for error in errors))

    def test_validate_integration_args_rejects_merge_recheck_at_open_pr_time(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "yes",
                "--integration-ref",
                "https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
                "--integration-status-checked-before-merge",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertTrue(any("`open_pr` 阶段不得把 `integration_status_checked_before_merge` 设为 `yes`" in error for error in errors))

    def test_validate_integration_args_rejects_local_only_external_integration_ref(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "none",
                "--integration-ref",
                "https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "--external-dependency",
                "none",
                "--merge-gate",
                "local_only",
                "--contract-surface",
                "none",
                "--joint-acceptance-needed",
                "no",
            ]
        )

        errors = validate_integration_args(args)

        self.assertTrue(any("纯本仓库事项必须显式使用 `integration_ref=none`" in error for error in errors))

    @patch(
        "scripts.integration_contract.run",
        return_value=subprocess.CompletedProcess(
            args=["gh"],
            returncode=0,
            stdout=json.dumps(
                {
                    "body": "\n".join(
                        [
                            "### integration_touchpoint",
                            "",
                            "active",
                            "",
                            "### shared_contract_changed",
                            "",
                            "yes",
                            "",
                            "### integration_ref",
                            "",
                            "https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test",
                            "",
                            "### external_dependency",
                            "",
                            "both",
                            "",
                            "### merge_gate",
                            "",
                            "integration_check_required",
                            "",
                            "### contract_surface",
                            "",
                            "runtime_modes",
                            "",
                            "### joint_acceptance_needed",
                            "",
                            "yes",
                        ]
                    )
                }
            ),
            stderr="",
        ),
    )
    def test_validate_integration_args_rejects_issue_canonical_mismatch(self, run_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "no",
                "--integration-ref",
                "https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertIn("`--shared-contract-changed` 与 Issue #105 中的 canonical integration 元数据不一致。", errors)
        self.assertGreaterEqual(run_mock.call_count, 1)

    @patch(
        "scripts.integration_contract.run",
        return_value=subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=json.dumps({"body": "### 摘要\n\n- no metadata"}), stderr=""),
    )
    def test_validate_integration_args_allows_legacy_issue_without_canonical_integration_metadata(self, run_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "none",
                "--integration-ref",
                "none",
                "--external-dependency",
                "none",
                "--merge-gate",
                "local_only",
            ]
        )

        errors = validate_integration_args(args)

        self.assertEqual(errors, [])
        run_mock.assert_called_once()

    @patch(
        "scripts.integration_contract.run",
        return_value=subprocess.CompletedProcess(args=["gh"], returncode=1, stdout="", stderr="boom"),
    )
    def test_validate_integration_args_rejects_issue_fetch_failure_for_canonical_integration(self, run_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "none",
                "--integration-ref",
                "none",
                "--external-dependency",
                "none",
                "--merge-gate",
                "local_only",
            ]
        )

        errors = validate_integration_args(args)

        self.assertIn("无法读取 Issue #105 的 canonical integration 元数据", errors[0])
        run_mock.assert_called_once()

    @patch(
        "scripts.integration_contract.run",
        return_value=subprocess.CompletedProcess(
            args=["gh"],
            returncode=0,
            stdout=json.dumps(
                {
                    "body": "\n".join(
                        [
                            "### integration_touchpoint",
                            "",
                            "active",
                            "",
                            "### shared_contract_changed",
                            "",
                            "no",
                            "",
                            "### integration_ref",
                            "",
                            "#12",
                            "",
                            "### external_dependency",
                            "",
                            "both",
                            "",
                            "### merge_gate",
                            "",
                            "integration_check_required",
                            "",
                            "### contract_surface",
                            "",
                            "runtime_modes",
                            "",
                            "### joint_acceptance_needed",
                            "",
                            "yes",
                        ]
                    )
                }
            ),
            stderr="",
        ),
    )
    @patch("scripts.common.default_github_repo", return_value="MC-and-his-Agents/Syvert")
    def test_validate_integration_args_accepts_equivalent_issue_ref_forms(self, default_repo_mock, run_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "no",
                "--integration-ref",
                "https://github.com/MC-and-his-Agents/Syvert/issues/12",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertEqual(errors, [])
        self.assertGreaterEqual(run_mock.call_count, 1)
        self.assertGreaterEqual(default_repo_mock.call_count, 1)

    @patch(
        "scripts.integration_contract.run",
        return_value=subprocess.CompletedProcess(
            args=["gh"],
            returncode=0,
            stdout=json.dumps(
                {
                    "body": "\n".join(
                        [
                            "### integration_touchpoint",
                            "",
                            "active",
                            "",
                            "### shared_contract_changed",
                            "",
                            "no",
                            "",
                            "### integration_ref",
                            "",
                            "https://github.com/orgs/MC-and-his-Agents/projects/3?itemId=PVTI_test&pane=issue",
                            "",
                            "### external_dependency",
                            "",
                            "both",
                            "",
                            "### merge_gate",
                            "",
                            "integration_check_required",
                            "",
                            "### contract_surface",
                            "",
                            "runtime_modes",
                            "",
                            "### joint_acceptance_needed",
                            "",
                            "yes",
                        ]
                    )
                }
            ),
            stderr="",
        ),
    )
    def test_validate_integration_args_accepts_equivalent_project_item_urls(self, run_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "no",
                "--integration-ref",
                "https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertEqual(errors, [])
        self.assertGreaterEqual(run_mock.call_count, 1)

    @patch(
        "scripts.integration_contract.fetch_integration_ref_live_state",
        return_value={
            "item_id": "PVTI_same",
            "organization": "mc-and-his-agents",
            "project_number": "3",
            "content_repo": "MC-and-his-Agents/Syvert",
            "content_issue_number": "12",
            "error": "",
        },
    )
    @patch(
        "scripts.integration_contract.run",
        return_value=subprocess.CompletedProcess(
            args=["gh"],
            returncode=0,
            stdout=json.dumps(
                {
                    "body": "\n".join(
                        [
                            "### integration_touchpoint",
                            "",
                            "active",
                            "",
                            "### shared_contract_changed",
                            "",
                            "no",
                            "",
                            "### integration_ref",
                            "",
                            "MC-and-his-Agents/Syvert#12",
                            "",
                            "### external_dependency",
                            "",
                            "both",
                            "",
                            "### merge_gate",
                            "",
                            "integration_check_required",
                            "",
                            "### contract_surface",
                            "",
                            "runtime_modes",
                            "",
                            "### joint_acceptance_needed",
                            "",
                            "yes",
                        ]
                    )
                }
            ),
            stderr="",
        ),
    )
    def test_validate_integration_args_accepts_equivalent_issue_and_project_item_refs(self, run_mock, fetch_live_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "no",
                "--integration-ref",
                "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertEqual(errors, [])
        self.assertGreaterEqual(run_mock.call_count, 1)
        self.assertEqual(args.integration_ref, "MC-and-his-Agents/Syvert#12")
        fetch_live_mock.assert_called_once_with("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same")

    @patch(
        "scripts.integration_contract.fetch_integration_ref_live_state",
        return_value={
            "item_id": "PVTI_same",
            "organization": "mc-and-his-agents",
            "project_number": "3",
            "content_repo": "MC-and-his-Agents/Syvert",
            "content_issue_number": "12",
            "error": "",
        },
    )
    @patch(
        "scripts.integration_contract.run",
        return_value=subprocess.CompletedProcess(
            args=["gh"],
            returncode=0,
            stdout=json.dumps(
                {
                    "body": "\n".join(
                        [
                            "### integration_touchpoint",
                            "",
                            "active",
                            "",
                            "### shared_contract_changed",
                            "",
                            "no",
                            "",
                            "### integration_ref",
                            "",
                            "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same",
                            "",
                            "### external_dependency",
                            "",
                            "both",
                            "",
                            "### merge_gate",
                            "",
                            "integration_check_required",
                            "",
                            "### contract_surface",
                            "",
                            "runtime_modes",
                            "",
                            "### joint_acceptance_needed",
                            "",
                            "yes",
                        ]
                    )
                }
            ),
            stderr="",
        ),
    )
    def test_validate_integration_args_accepts_equivalent_issue_ref_for_project_item_canonical(
        self, run_mock, fetch_live_mock
    ) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "no",
                "--integration-ref",
                "MC-and-his-Agents/Syvert#12",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertEqual(errors, [])
        self.assertEqual(
            args.integration_ref,
            "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same",
        )
        fetch_live_mock.assert_called_once_with("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same")

    @patch(
        "scripts.integration_contract.run",
        return_value=subprocess.CompletedProcess(
            args=["gh"],
            returncode=0,
            stdout=json.dumps(
                {
                    "body": "\n".join(
                        [
                            "### integration_touchpoint",
                            "",
                            "active",
                            "",
                            "### shared_contract_changed",
                            "",
                            "no",
                            "",
                            "### integration_ref",
                            "",
                            "MC-and-his-Agents/Syvert#12",
                            "",
                            "### external_dependency",
                            "",
                            "both",
                            "",
                            "### merge_gate",
                            "",
                            "integration_check_required",
                            "",
                            "### contract_surface",
                            "",
                            "runtime_modes",
                            "",
                            "### joint_acceptance_needed",
                            "",
                            "yes",
                        ]
                    )
                }
            ),
            stderr="",
        ),
    )
    def test_validate_integration_args_rejects_non_equivalent_integration_ref_without_rewriting_input(self, run_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "no",
                "--integration-ref",
                "https://github.com/MC-and-his-Agents/WebEnvoy/issues/999",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
            ]
        )

        errors = validate_integration_args(args)

        self.assertIn("`--integration-ref` 与 Issue #105 中的 canonical integration 元数据不一致。", errors)
        self.assertEqual(args.integration_ref, "https://github.com/MC-and-his-Agents/WebEnvoy/issues/999")
        self.assertGreaterEqual(run_mock.call_count, 1)

    def test_build_issue_summary_extracts_minimal_high_value_issue_context(self) -> None:
        payload = {
            "body": "\n".join(
                [
                    "## Goal",
                    "",
                    "- 对齐模板",
                    "",
                    "## Scope",
                    "",
                    "- 调整 open_pr 和 guardian",
                    "",
                    "## Out of Scope",
                    "",
                    "- 不改 merge_pr",
                ]
            )
        }

        with patch(
            "scripts.open_pr.run",
            return_value=type("Completed", (), {"returncode": 0, "stdout": __import__("json").dumps(payload)})(),
        ):
            summary = build_issue_summary(25)

        self.assertIn("## Goal", summary)
        self.assertIn("## Scope", summary)
        self.assertIn("## Out of Scope", summary)

    @patch("scripts.open_pr.default_github_repo", return_value="MC-and-his-Agents/Syvert")
    @patch("scripts.open_pr.run")
    def test_build_issue_summary_binds_issue_reads_to_canonical_repo(self, run_mock, default_repo_mock) -> None:
        run_mock.return_value = type(
            "Completed",
            (),
            {"returncode": 0, "stdout": json.dumps({"body": "## Goal\n\n- 对齐 contract"}), "stderr": ""},
        )()

        summary = build_issue_summary(25)

        self.assertIn("## Goal", summary)
        run_mock.assert_called_once_with(
            ["gh", "issue", "view", "25", "--repo", "MC-and-his-Agents/Syvert", "--json", "body"],
            cwd=ANY,
            check=False,
        )
        default_repo_mock.assert_called_once_with()

    def test_extract_issue_summary_sections_supports_issue_form_heading_aliases(self) -> None:
        body = "\n".join(
            [
                "### 摘要",
                "",
                "目标：收口本轮治理改造。",
                "",
                "### integration_touchpoint",
                "",
                "none",
                "",
                "### 治理目标",
                "",
                "补齐跨仓协同插槽。",
            ]
        )

        sections = extract_issue_summary_sections(body)

        self.assertIn("Goal", sections)
        self.assertIn("目标：收口本轮治理改造。", sections["Goal"])
        self.assertIn("补齐跨仓协同插槽。", sections["Goal"])
        self.assertNotIn("integration_touchpoint", sections)

    def test_extract_issue_canonical_integration_fields_preserves_issue_form_metadata(self) -> None:
        body = "\n".join(
            [
                "### integration_touchpoint",
                "",
                "active",
                "",
                "### shared_contract_changed",
                "",
                "yes",
                "",
                "### integration_ref",
                "",
                "owner/repo#12",
                "",
                "### merge_gate",
                "",
                "integration_check_required",
            ]
        )

        payload = extract_issue_canonical_integration_fields(body)

        self.assertEqual(payload["integration_touchpoint"], "active")
        self.assertEqual(payload["shared_contract_changed"], "yes")
        self.assertEqual(payload["integration_ref"], "owner/repo#12")
        self.assertEqual(payload["merge_gate"], "integration_check_required")

    def test_build_issue_summary_renders_chinese_issue_form_sections(self) -> None:
        payload = {
            "body": "\n".join(
                [
                    "### 摘要",
                    "",
                    "目标：统一执行入口。",
                    "",
                    "### 影响载体",
                    "",
                    "- WORKFLOW.md",
                    "",
                    "### Formal Spec 套件",
                    "",
                    "- spec.md",
                ]
            )
        }

        with patch(
            "scripts.open_pr.run",
            return_value=type("Completed", (), {"returncode": 0, "stdout": __import__("json").dumps(payload)})(),
        ):
            summary = build_issue_summary(105)

        self.assertIn("## Goal", summary)
        self.assertIn("## Scope", summary)
        self.assertIn("## Required Outcomes", summary)
        self.assertIn("目标：统一执行入口。", summary)
        self.assertIn("- WORKFLOW.md", summary)
        self.assertIn("- spec.md", summary)

    def test_legacy_filename_exec_plan_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "governance-stack-v1.md").write_text(
                "\n".join(
                    [
                        "# plan",
                        "",
                        "## 事项上下文",
                        "",
                        "- Issue：`#6`",
                        "- item_key：`FR-0001-governance-stack-v1`",
                        "- item_type：`FR`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S13`",
                        "- 关联 spec：`docs/specs/FR-0001-governance-stack-v1/`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                6,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S13",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_build_body_populates_integration_check_fields(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "yes",
                "--integration-ref",
                "https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
                "--integration-status-checked-before-merge",
                "no",
            ]
        )

        body = build_body(args, [])

        self.assertIn("- integration_touchpoint: active", body)
        self.assertIn("- shared_contract_changed: yes", body)
        self.assertIn("- integration_ref: https://github.com/MC-and-his-Agents/WebEnvoy/issues/466", body)
        self.assertIn("- merge_gate: integration_check_required", body)
        self.assertIn("- contract_surface: runtime_modes", body)

    def test_build_body_populates_review_artifacts_section(self) -> None:
        args = parse_args(["--class", "governance"])

        body = build_body(args, [])

        self.assertIn("- Active exec-plan: 未定位到 active exec-plan", body)
        self.assertIn("- Governing spec / bootstrap contract: 未定位到 governing artifact", body)
        self.assertIn("- Review artifact: `code_review.md`", body)
        self.assertIn(
            "- Validation evidence: 见 `## 验证`，由受控流程补充已执行验证命令或验证 artifact。",
            body,
        )

    def test_governing_artifact_label_requires_concrete_locator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, item_key="GOV-0015-item-context-gate")
            exec_plan = {
                "item_key": "GOV-0015-item-context-gate",
                "item_type": "GOV",
                "exec_plan": str(repo / "docs/exec-plans/GOV-0015-item-context-gate.md"),
            }

            self.assertEqual(governing_artifact_label(exec_plan, repo_root=repo), "")

    def test_build_body_uses_spec_review_artifact_for_spec_scope_changes(self) -> None:
        args = parse_args(["--class", "governance"])

        body = build_body(args, [".loom/specs/INIT-0001/spec.md"])

        self.assertIn("- Review artifact: `spec_review.md`, `code_review.md`", body)

    def test_has_formal_spec_core_file_changes_accepts_loom_spec_artifacts(self) -> None:
        self.assertTrue(has_formal_spec_core_file_changes([".loom/specs/INIT-0001/spec.md"]))
        self.assertTrue(has_formal_spec_core_file_changes([".loom/specs/INIT-0001/implementation-contract.md"]))

    def test_validate_pr_preflight_rejects_governance_pr_that_touches_loom_spec_without_formal_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "docs/exec-plans").mkdir(parents=True)
            (repo / "docs/exec-plans/GOV-0001-shadow-parity-hardening.md").write_text(
                "\n".join(
                    [
                        "# Exec Plan",
                        "",
                        "- item_key：`GOV-0001-shadow-parity-hardening`",
                        "- Issue：`#6`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S13`",
                        "- active 收口事项：`GOV-0001-shadow-parity-hardening`",
                        "- 状态：`active`",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                6,
                "GOV-0001-shadow-parity-hardening",
                "GOV",
                "v0.1.0",
                "2026-S13",
                [".loom/specs/INIT-0001/spec.md"],
                repo_root=repo,
            )

        self.assertTrue(any("变更 formal spec 套件时" in error for error in errors))

    @patch(
        "scripts.open_pr.resolve_issue_canonical_integration",
        return_value=(
            {
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "MC-and-his-Agents/Syvert#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
            None,
        ),
    )
    @patch(
        "scripts.integration_contract.fetch_integration_ref_live_state",
        return_value={
            "item_id": "PVTI_same",
            "organization": "mc-and-his-agents",
            "project_number": "3",
            "content_repo": "MC-and-his-Agents/Syvert",
            "content_issue_number": "12",
            "error": "",
        },
    )
    def test_build_body_canonicalizes_equivalent_integration_ref_to_issue_carrier(self, fetch_live_mock, resolve_issue_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "no",
                "--integration-ref",
                "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
                "--integration-status-checked-before-merge",
                "no",
            ]
        )

        body = build_body(args, [])

        self.assertIn("- integration_ref: MC-and-his-Agents/Syvert#12", body)
        self.assertNotIn("PVTI_same", body)
        resolve_issue_mock.assert_called_once_with(105)
        fetch_live_mock.assert_called_once_with("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same")

    @patch(
        "scripts.integration_contract.fetch_integration_ref_live_state",
        return_value={
            "item_id": "PVTI_same",
            "organization": "mc-and-his-agents",
            "project_number": "3",
            "content_repo": "MC-and-his-Agents/Syvert",
            "content_issue_number": "12",
            "error": "",
        },
    )
    @patch(
        "scripts.open_pr.resolve_issue_canonical_integration",
        return_value=(
            {
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
            None,
        ),
    )
    def test_build_body_canonicalizes_equivalent_issue_ref_to_project_item_carrier(self, resolve_issue_mock, fetch_live_mock) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "105",
                "--integration-touchpoint",
                "active",
                "--shared-contract-changed",
                "no",
                "--integration-ref",
                "MC-and-his-Agents/Syvert#12",
                "--external-dependency",
                "both",
                "--merge-gate",
                "integration_check_required",
                "--contract-surface",
                "runtime_modes",
                "--joint-acceptance-needed",
                "yes",
                "--integration-status-checked-before-pr",
                "yes",
                "--integration-status-checked-before-merge",
                "no",
            ]
        )

        body = build_body(args, [])

        self.assertIn("- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same", body)
        self.assertNotIn("- integration_ref: MC-and-his-Agents/Syvert#12", body)
        resolve_issue_mock.assert_called_once_with(105)
        fetch_live_mock.assert_called_once_with("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same")

    def test_inactive_exec_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0015-item-context-gate.md"
            exec_plan.write_text(exec_plan.read_text(encoding="utf-8") + "- 状态：`inactive for PR #18`\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少 active `exec-plan`" in error for error in errors))

    def test_duplicate_exec_plan_metadata_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0015-item-context-gate.md"
            exec_plan.write_text(
                exec_plan.read_text(encoding="utf-8") + "- release：`v0.2.0`\n",
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("重复键" in error for error in errors))

    def test_unrelated_duplicate_exec_plan_metadata_does_not_block_current_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, related_decision="docs/decisions/ADR-0001.md")
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "broken-other.md").write_text(
                "\n".join(
                    [
                        "# broken",
                        "",
                        "## 关联信息",
                        "",
                        "- item_key：`GOV-0099-other`",
                        "- item_key：`GOV-0099-other-shadow`",
                        "- Issue：`#99`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#19", item_key="GOV-0015-item-context-gate")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_duplicate_metadata_in_secondary_file_for_same_item_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "shadow.md").write_text(
                "\n".join(
                    [
                        "# shadow",
                        "",
                        "## 关联信息",
                        "",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- Issue：`#19`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- release：`v0.2.0`",
                        "- sprint：`2026-S14`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("重复键" in error for error in errors))

    def test_duplicate_metadata_in_secondary_file_is_rejected_even_when_duplicate_precedes_item_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "shadow.md").write_text(
                "\n".join(
                    [
                        "# shadow",
                        "",
                        "## 关联信息",
                        "",
                        "- release：`v0.1.0`",
                        "- release：`v0.2.0`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- Issue：`#19`",
                        "- item_type：`GOV`",
                        "- sprint：`2026-S14`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("重复键" in error for error in errors))

    def test_duplicate_active_exec_plans_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "legacy-duplicate.md").write_text(
                "\n".join(
                    [
                        "# duplicate",
                        "",
                        "## 事项上下文",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("多个 active `exec-plan`" in error for error in errors))

    def test_different_active_item_under_same_issue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plans = repo / "docs" / "exec-plans"
            (exec_plans / "other-item.md").write_text(
                "\n".join(
                    [
                        "# other",
                        "",
                        "## 事项上下文",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0014-release-sprint-structure`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "- active 收口事项：`GOV-0014-release-sprint-structure`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("当前 `Issue` 存在多个 active `exec-plan`" in error for error in errors))

    def test_governance_without_issue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            errors = validate_pr_preflight("governance", None, None, None, None, None, ["AGENTS.md"], repo_root=repo)
        self.assertTrue(any("缺少完整事项上下文" in error for error in errors))

    def test_issue_must_match_current_worktree_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch("scripts.open_pr.load_worktree_binding_for_branch", return_value={"issue": 18, "branch": "issue-19-demo"}):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("branch/worktree 绑定的事项不一致" in error for error in errors))

    def test_worktree_path_must_match_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            other = repo / "other"
            other.mkdir()
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch(
                        "scripts.open_pr.load_worktree_binding_for_branch",
                        return_value={"issue": 19, "branch": "issue-19-demo", "path": str(other)},
                    ):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("worktree `path` 不一致" in error for error in errors))

    def test_binding_check_is_skipped_for_foreign_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                with patch(
                    "scripts.open_pr.load_worktree_binding_for_branch",
                    return_value={"issue": 18, "branch": "issue-19-demo"},
                ):
                    errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertEqual(errors, [])

    def test_branch_read_failure_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", side_effect=CommandError(["git"], 1, "", "boom")):
                    errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("无法识别当前分支" in error for error in errors))

    def test_duplicate_branch_bindings_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch(
                        "scripts.open_pr.load_worktree_binding_for_branch",
                        return_value={"conflict": "multiple_branch_bindings", "branch": "issue-19-demo"},
                    ):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("多个 worktree 绑定" in error for error in errors))

    def test_invalid_worktree_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch(
                        "scripts.open_pr.load_worktree_binding_for_branch",
                        return_value={"conflict": "invalid_worktree_state", "branch": "issue-19-demo"},
                    ):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("`worktrees.json` 已损坏" in error for error in errors))

    def test_invalid_binding_issue_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            with patch("scripts.open_pr.REPO_ROOT", repo):
                with patch("scripts.open_pr.git_current_branch", return_value="issue-19-demo"):
                    with patch(
                        "scripts.open_pr.load_worktree_binding_for_branch",
                        return_value={"issue": "not-a-number", "branch": "issue-19-demo"},
                    ):
                        errors = validate_current_worktree_binding(19, repo_root=repo)
        self.assertTrue(any("`issue` 值非法" in error for error in errors))

    def test_missing_active_exec_plan_for_issue_has_precise_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            exec_plan = repo / "docs" / "exec-plans" / "GOV-0015-item-context-gate.md"
            exec_plan.write_text(exec_plan.read_text(encoding="utf-8") + "- 状态：`inactive for PR #18`\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("当前事项缺少 active `exec-plan`" in error or "当前 `Issue` 缺少 active `exec-plan`" in error for error in errors))

    def test_missing_release_or_sprint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo)
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                None,
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少完整事项上下文" in error for error in errors))

    def test_invalid_item_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, item_key="GOV-0015-item-context-gate")
            errors = validate_pr_preflight(
                "governance",
                19,
                "FR-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("`item_key` 必须匹配" in error for error in errors))

    def test_missing_exec_plan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少 active `exec-plan`" in error for error in errors))

    def test_mismatched_exec_plan_context_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, release="v0.2.0")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("active `exec-plan` 的 `release`" in error for error in errors))

    def test_active_item_key_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, active_item_key="GOV-0014-release-sprint-structure")
            errors = validate_pr_preflight(
                "governance",
                19,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少 active `exec-plan`" in error or "active 收口事项" in error for error in errors))

    def test_core_item_without_spec_or_bootstrap_contract_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(repo, item_key="FR-0001-governance-stack-v1", issue="#1", item_type="FR")
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/process/delivery-funnel.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_core_item_with_valid_formal_spec_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_governance_repo_scan_accepts_valid_bound_formal_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_unrelated_formal_spec_cannot_replace_bound_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-9999-missing/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("formal spec 或 bootstrap contract" in error or "formal spec 套件" in error for error in errors))

    def test_unrelated_touched_formal_spec_cannot_replace_invalid_bound_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-9999-missing/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertTrue(any("formal spec 或 bootstrap contract" in error or "formal spec 套件" in error for error in errors))

    def test_governance_without_bound_spec_cannot_fallback_to_unrelated_repo_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("formal spec 或 bootstrap contract" in error or "formal spec 套件" in error for error in errors))

    def test_legacy_bound_spec_file_path_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/spec.md",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_bound_formal_spec_rejects_unrelated_touched_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            write_formal_spec_suite(repo, suite_name="FR-9999-unrelated", with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                [
                    "docs/specs/FR-0001-governance-stack-v1/spec.md",
                    "docs/specs/FR-9999-unrelated/spec.md",
                ],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_bound_formal_spec_accepts_only_its_own_touched_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_bound_formal_spec_accepts_gov_0029_delete_only_legacy_todo_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0029-remove-legacy-todo-md",
                issue="#58",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0029-remove-legacy-todo-md",
                related_spec="docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/",
                related_decision="docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md",
            )
            write_formal_spec_suite(repo, suite_name="FR-0003-github-delivery-structure-and-repo-semantic-split", with_todo=False)
            write_formal_spec_suite(repo, suite_name="FR-0001-governance-stack-v1", with_todo=True)
            write_formal_spec_suite(repo, suite_name="FR-0002-content-detail-runtime-v0-1", with_todo=True)
            (repo / "docs" / "specs" / "FR-0001-governance-stack-v1" / "risks.md").write_text("# risks\n", encoding="utf-8")
            write_decision(
                repo,
                "docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md",
                issue="#58",
                item_key="GOV-0029-remove-legacy-todo-md",
            )
            plan = repo / "docs" / "exec-plans" / "GOV-0029-remove-legacy-todo-md.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`\n",
                    "- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`\n- 额外关联 specs：docs/specs/FR-0001-governance-stack-v1/, docs/specs/FR-0002-content-detail-runtime-v0-1/\n",
                ),
                encoding="utf-8",
            )
            (repo / "docs" / "specs" / "FR-0001-governance-stack-v1" / "TODO.md").unlink()
            (repo / "docs" / "specs" / "FR-0002-content-detail-runtime-v0-1" / "TODO.md").unlink()
            errors = validate_pr_preflight(
                "governance",
                58,
                "GOV-0029-remove-legacy-todo-md",
                "GOV",
                "v0.2.0",
                "2026-S15",
                [
                    "docs/specs/FR-0001-governance-stack-v1/spec.md",
                    "docs/specs/FR-0001-governance-stack-v1/plan.md",
                    "docs/specs/FR-0001-governance-stack-v1/risks.md",
                    "docs/specs/FR-0001-governance-stack-v1/TODO.md",
                    "docs/specs/FR-0002-content-detail-runtime-v0-1/TODO.md",
                ],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_governance_pr_rejects_exec_plan_only_additional_spec_binding_without_matching_todo_deletions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0029-remove-legacy-todo-md",
                issue="#58",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0029-remove-legacy-todo-md",
                related_spec="docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/",
                related_decision="docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md",
            )
            write_formal_spec_suite(repo, suite_name="FR-0003-github-delivery-structure-and-repo-semantic-split", with_todo=False)
            write_formal_spec_suite(repo, suite_name="FR-0001-governance-stack-v1", with_todo=True)
            write_formal_spec_suite(repo, suite_name="FR-0002-content-detail-runtime-v0-1", with_todo=True)
            write_decision(
                repo,
                "docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md",
                issue="#58",
                item_key="GOV-0029-remove-legacy-todo-md",
            )
            plan = repo / "docs" / "exec-plans" / "GOV-0029-remove-legacy-todo-md.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`\n",
                    "- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`\n- 额外关联 specs：docs/specs/FR-0001-governance-stack-v1/, docs/specs/FR-0002-content-detail-runtime-v0-1/\n",
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                58,
                "GOV-0029-remove-legacy-todo-md",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["docs/exec-plans/GOV-0029-remove-legacy-todo-md.md"],
                repo_root=repo,
            )
        self.assertTrue(errors)

    def test_governance_pr_rejects_invalid_additional_spec_binding_on_docs_only_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            plan = repo / "docs" / "exec-plans" / "GOV-0028-harness-compat-migration.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- 关联 spec：`docs/specs/FR-0001-governance-stack-v1/`\n",
                    "- 关联 spec：`docs/specs/FR-0001-governance-stack-v1/`\n- 额外关联 specs：`docs/specs/_template/`\n",
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(errors)

    def test_spec_pr_rejects_additional_spec_binding_for_non_governance_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            write_formal_spec_suite(repo, suite_name="FR-9999-unrelated", with_todo=False)
            plan = repo / "docs" / "exec-plans" / "FR-0001-governance-stack-v1.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- 关联 spec：`docs/specs/FR-0001-governance-stack-v1/`\n",
                    "- 关联 spec：`docs/specs/FR-0001-governance-stack-v1/`\n- 额外关联 specs：`docs/specs/FR-9999-unrelated/`\n",
                ),
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                [
                    "docs/specs/FR-0001-governance-stack-v1/spec.md",
                    "docs/specs/FR-9999-unrelated/spec.md",
                ],
                repo_root=repo,
            )
        self.assertTrue(errors)

    def test_bound_formal_spec_must_be_reviewable_not_just_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            suite_dir = repo / "docs" / "specs" / "FR-0001-governance-stack-v1"
            suite_dir.mkdir(parents=True, exist_ok=True)
            (suite_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
            (suite_dir / "plan.md").write_text("# plan\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_template_spec_binding_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_spec="docs/specs/_template/",
            )
            template_dir = repo / "docs" / "specs" / "_template"
            template_dir.mkdir(parents=True, exist_ok=True)
            (template_dir / "spec.md").write_text("# spec\n", encoding="utf-8")
            (template_dir / "plan.md").write_text("# plan\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "governance",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("formal spec 或 bootstrap contract" in error or "formal spec 套件" in error for error in errors))

    def test_governance_with_bootstrap_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#5", item_key="GOV-0015-item-context-gate")
            write_exec_plan(repo, issue="#5", related_decision="docs/decisions/ADR-0001.md")
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_legacy_placeholder_related_spec_still_uses_bootstrap_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#5", item_key="GOV-0015-item-context-gate")
            write_exec_plan(
                repo,
                issue="#5",
                related_spec="无（治理文档事项）",
                related_decision="docs/decisions/ADR-0001.md",
            )
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_governance_formal_spec_mode_cannot_fallback_to_bootstrap_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#5", item_key="GOV-0015-item-context-gate")
            write_exec_plan(
                repo,
                issue="#5",
                related_spec="docs/specs/FR-9999-missing/",
                related_decision="docs/decisions/ADR-0001.md",
            )
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_governance_with_unrelated_bootstrap_decision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-GOV-9999-unrelated.md").write_text(
                """# ADR-GOV-9999

- Issue：`#999`
- item_key：`GOV-9999-unrelated`
""",
                encoding="utf-8",
            )
            write_exec_plan(repo, issue="#5", related_decision="docs/decisions/ADR-GOV-9999-unrelated.md")
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_governance_bootstrap_contract_requires_valid_current_item_decision_binding(self) -> None:
        scenarios = (
            ("missing", None),
            ("nonexistent", "docs/decisions/ADR-0001-missing.md"),
            ("out_of_repo", "../outside-decision.md"),
            ("wrong_dir", "docs/exec-plans/GOV-0015-item-context-gate.md"),
            ("metadata_free", "docs/decisions/ADR-0002-empty.md"),
            ("duplicate_metadata", "docs/decisions/ADR-0003-duplicate.md"),
        )
        for label, related_decision in scenarios:
            with self.subTest(case=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    repo = Path(temp_dir)
                    if related_decision and related_decision.startswith("docs/decisions/"):
                        (repo / "docs" / "decisions").mkdir(parents=True)
                    if label == "metadata_free":
                        (repo / "docs" / "decisions" / "ADR-0002-empty.md").write_text("# ADR\n", encoding="utf-8")
                    if label == "duplicate_metadata":
                        (repo / "docs" / "decisions" / "ADR-0003-duplicate.md").write_text(
                            """# ADR\n\n- Issue：`#5`\n- Issue：`#6`\n- item_key：`GOV-0015-item-context-gate`\n""",
                            encoding="utf-8",
                        )
                    write_exec_plan(repo, issue="#5", related_decision=related_decision)
                    errors = validate_pr_preflight(
                        "governance",
                        5,
                        "GOV-0015-item-context-gate",
                        "GOV",
                        "v0.1.0",
                        "2026-S14",
                        ["AGENTS.md"],
                        repo_root=repo,
                    )
                self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_unrelated_repo_bootstrap_contract_cannot_replace_current_item_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_decision(repo, "docs/decisions/ADR-0001.md", issue="#5", item_key="GOV-0015-item-context-gate")
            write_exec_plan(repo, issue="#5")
            write_exec_plan(
                repo,
                item_key="GOV-9999-unrelated-bootstrap",
                issue="#9999",
                active_item_key="GOV-9999-unrelated-bootstrap",
                related_decision="docs/decisions/ADR-0001.md",
            )
            errors = validate_pr_preflight(
                "governance",
                5,
                "GOV-0015-item-context-gate",
                "GOV",
                "v0.1.0",
                "2026-S14",
                ["AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_spec_class_without_spec_changes_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "docs" / "decisions").mkdir(parents=True)
            (repo / "docs" / "decisions" / "ADR-0001.md").write_text("# adr\n", encoding="utf-8")
            write_exec_plan(repo, item_key="FR-0003-demo-spec", issue="#3", item_type="FR")
            errors = validate_pr_preflight(
                "spec",
                3,
                "FR-0003-demo-spec",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["code_review.md"],
                repo_root=repo,
            )
        self.assertTrue(any("核心文件变更" in error or "正式规约区变更" in error for error in errors))

    def test_spec_pr_rejects_live_legacy_todo_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=True)
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/TODO.md"],
                repo_root=repo,
            )
        self.assertTrue(any("请删除该文件" in error for error in errors))

    def test_governance_pr_rejects_invalid_foreign_exec_plan_rewrite_even_with_todo_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0029-remove-legacy-todo-md",
                issue="#58",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0029-remove-legacy-todo-md",
                related_spec="docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/",
                related_decision="docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md",
            )
            write_formal_spec_suite(repo, suite_name="FR-0003-github-delivery-structure-and-repo-semantic-split", with_todo=False)
            write_formal_spec_suite(repo, suite_name="FR-0002-content-detail-runtime-v0-1", with_todo=True)
            write_decision(
                repo,
                "docs/decisions/ADR-GOV-0029-remove-legacy-todo-md.md",
                issue="#58",
                item_key="GOV-0029-remove-legacy-todo-md",
            )
            plan = repo / "docs" / "exec-plans" / "GOV-0029-remove-legacy-todo-md.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace(
                    "- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`\n",
                    "- 关联 spec：`docs/specs/FR-0003-github-delivery-structure-and-repo-semantic-split/`\n- 额外关联 specs：docs/specs/FR-0002-content-detail-runtime-v0-1/\n",
                ),
                encoding="utf-8",
            )
            write_decision(
                repo,
                "docs/decisions/ADR-0001-governance-bootstrap-contract.md",
                issue="#38",
                item_key="FR-0002-content-detail-runtime-v0-1",
            )
            write_exec_plan(
                repo,
                item_key="FR-0002-content-detail-runtime-v0-1",
                issue="#38",
                item_type="FR",
                release="v0.1.0",
                sprint="2026-S15",
                active_item_key="FR-0002-content-detail-runtime-v0-1",
                related_spec="docs/specs/FR-0002-content-detail-runtime-v0-1/",
                related_decision="docs/decisions/ADR-0001-governance-bootstrap-contract.md",
            )
            foreign = repo / "docs" / "exec-plans" / "FR-0002-content-detail-runtime-v0-1.md"
            foreign.write_text(
                foreign.read_text(encoding="utf-8").replace("# plan", "# rewritten"),
                encoding="utf-8",
            )
            (repo / "docs" / "specs" / "FR-0002-content-detail-runtime-v0-1" / "TODO.md").unlink()
            errors = validate_pr_preflight(
                "governance",
                58,
                "GOV-0029-remove-legacy-todo-md",
                "GOV",
                "v0.2.0",
                "2026-S15",
                [
                    "docs/exec-plans/FR-0002-content-detail-runtime-v0-1.md",
                    "docs/specs/FR-0002-content-detail-runtime-v0-1/TODO.md",
                ],
                repo_root=repo,
            )
        self.assertTrue(any("最小终态" in error for error in errors))

    def test_spec_pr_accepts_delete_only_legacy_todo_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=True)
            (repo / "docs" / "specs" / "FR-0001-governance-stack-v1" / "TODO.md").unlink()
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/TODO.md"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_spec_pr_rejects_adjunct_only_suite_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
            )
            write_formal_spec_suite(repo, with_todo=False)
            adjunct = repo / "docs" / "specs" / "FR-0001-governance-stack-v1" / "contracts" / "README.md"
            adjunct.parent.mkdir(parents=True, exist_ok=True)
            adjunct.write_text("# contracts\n", encoding="utf-8")
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/contracts/README.md"],
                repo_root=repo,
            )
        self.assertTrue(any("核心文件变更" in error for error in errors))

    def test_unbound_fr_item_requires_its_own_touched_formal_spec_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
            )
            write_formal_spec_suite(repo, suite_name="FR-9999-unrelated", with_todo=False)
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-9999-unrelated/spec.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_legacy_implementation_pr_accepts_existing_local_formal_spec_suite_for_fr_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "implementation",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["scripts/tool.py"],
                repo_root=repo,
            )
        self.assertEqual(errors, [])

    def test_implementation_pr_accepts_legacy_metadata_free_adr_for_formal_spec_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0002-content-detail-runtime-v0-1",
                issue="#38",
                item_type="FR",
                active_item_key="FR-0002-content-detail-runtime-v0-1",
                related_spec="docs/specs/FR-0002-content-detail-runtime-v0-1/",
                related_decision="docs/decisions/ADR-0001-governance-bootstrap-contract.md",
            )
            write_formal_spec_suite(repo, suite_name="FR-0002-content-detail-runtime-v0-1", with_todo=False)
            (repo / "docs" / "decisions").mkdir(parents=True, exist_ok=True)
            (repo / "docs" / "decisions" / "ADR-0001-governance-bootstrap-contract.md").write_text(
                "# ADR-0001 bootstrap\n",
                encoding="utf-8",
            )
            errors = validate_pr_preflight(
                "implementation",
                38,
                "FR-0002-content-detail-runtime-v0-1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["scripts/tool.py"],
                repo_root=repo,
                validate_worktree_binding_check=False,
            )
        self.assertEqual(errors, [])

    def test_formal_spec_mode_rejects_inconsistent_optional_related_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
                related_spec="docs/specs/FR-0001-governance-stack-v1/",
                related_decision="docs/decisions/ADR-0003-shared.md",
            )
            write_formal_spec_suite(repo, with_todo=False)
            write_decision(repo, "docs/decisions/ADR-0003-shared.md", issue="#2", item_key="GOV-0002-other")
            errors = validate_pr_preflight(
                "spec",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_spec_pr_does_not_accept_bootstrap_contract_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="GOV-0028-harness-compat-migration",
                issue="#57",
                item_type="GOV",
                release="v0.2.0",
                sprint="2026-S15",
                active_item_key="GOV-0028-harness-compat-migration",
                related_decision="docs/decisions/ADR-0003-example.md",
            )
            write_decision(
                repo,
                "docs/decisions/ADR-0003-example.md",
                issue="#57",
                item_key="GOV-0028-harness-compat-migration",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "spec",
                57,
                "GOV-0028-harness-compat-migration",
                "GOV",
                "v0.2.0",
                "2026-S15",
                ["docs/specs/FR-0001-governance-stack-v1/spec.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error for error in errors))

    def test_governance_pr_does_not_accept_unbound_fr_local_formal_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
            )
            write_formal_spec_suite(repo, with_todo=False)
            errors = validate_pr_preflight(
                "governance",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["docs/AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_implementation_pr_requires_local_formal_input_for_fr_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="FR-0001-governance-stack-v1",
                issue="#1",
                item_type="FR",
                active_item_key="FR-0001-governance-stack-v1",
            )
            errors = validate_pr_preflight(
                "implementation",
                1,
                "FR-0001-governance-stack-v1",
                "FR",
                "v0.1.0",
                "2026-S14",
                ["scripts/tool.py"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_implementation_pr_requires_formal_input_for_hotfix_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="HOTFIX-0001-critical-patch",
                issue="#1",
                item_type="HOTFIX",
                active_item_key="HOTFIX-0001-critical-patch",
            )
            errors = validate_pr_preflight(
                "implementation",
                1,
                "HOTFIX-0001-critical-patch",
                "HOTFIX",
                "v0.1.0",
                "2026-S14",
                ["scripts/tool.py"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_implementation_pr_requires_formal_input_for_chore_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            write_exec_plan(
                repo,
                item_key="CHORE-0001-doc-refresh",
                issue="#1",
                item_type="CHORE",
                active_item_key="CHORE-0001-doc-refresh",
            )
            errors = validate_pr_preflight(
                "implementation",
                1,
                "CHORE-0001-doc-refresh",
                "CHORE",
                "v0.1.0",
                "2026-S14",
                ["docs/AGENTS.md"],
                repo_root=repo,
            )
        self.assertTrue(any("缺少绑定 formal spec 输入" in error or "formal spec 或 bootstrap contract" in error for error in errors))

    def test_build_body_contains_item_context(self) -> None:
        args = parse_args(
            [
                "--class",
                "governance",
                "--issue",
                "19",
                "--item-key",
                "GOV-0015-item-context-gate",
                "--item-type",
                "GOV",
                "--release",
                "v0.1.0",
                "--sprint",
                "2026-S14",
                "--dry-run",
            ]
        )
        body = build_body(args, ["AGENTS.md"])
        self.assertIn("item_key: `GOV-0015-item-context-gate`", body)
        self.assertIn("item_type: `GOV`", body)
        self.assertIn("release: `v0.1.0`", body)
        self.assertIn("sprint: `2026-S14`", body)
        self.assertIn("- 审查关注：", body)
        self.assertNotIn("## 变更文件", body)
        self.assertNotIn("## 检查清单", body)


if __name__ == "__main__":
    unittest.main()
