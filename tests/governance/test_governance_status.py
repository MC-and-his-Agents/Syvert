from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import governance_status


class GovernanceStatusTests(unittest.TestCase):
    def test_aggregates_guardian_reviewer_and_worktree_state(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {"7": {"verdict": "APPROVE"}}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {"7": {"head_sha": "abc"}}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={
                            "headRefOid": "sha-1",
                            "headRefName": "feature/x",
                            "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                        },
                    ):
                        with patch("scripts.governance_status.find_latest_guardian_result", return_value={"verdict": "APPROVE", "head_sha": "sha-1"}):
                            with patch("scripts.governance_status.fetch_checks_summary", return_value=[{"name": "check", "bucket": "pass", "state": "SUCCESS"}]):
                                with patch(
                                    "scripts.governance_status.load_item_context_from_exec_plan",
                                    return_value={
                                        "Issue": "19",
                                        "item_key": "GOV-0015-item-context-gate",
                                        "item_type": "GOV",
                                        "release": "v0.1.0",
                                        "sprint": "2026-S14",
                                        "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
                                    },
                                ):
                                    payload = governance_status.build_status_payload(pr_number=7)

        self.assertEqual(payload["guardian"]["verdict"], "APPROVE")
        self.assertEqual(payload["review_poller"]["head_sha"], "abc")
        self.assertEqual(len(payload["worktrees"]), 1)
        self.assertEqual(payload["checks"][0]["name"], "check")
        self.assertEqual(payload["item_context"]["item_key"], "GOV-0015-item-context-gate")

    def test_pr_status_passes_current_body_to_guardian_lookup_and_requires_body_bound_cache(self) -> None:
        pr_body = "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n"
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": pr_body},
                    ):
                        with patch(
                            "scripts.governance_status.find_latest_guardian_result",
                            return_value=None,
                        ) as find_latest_guardian_result_mock:
                            with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                payload = governance_status.build_status_payload(pr_number=7)

        find_latest_guardian_result_mock.assert_called_once_with(
            7,
            "sha-1",
            body=pr_body,
            require_body_bound=True,
            path=governance_status.GUARDIAN_STATE_FILE,
        )
        self.assertEqual(payload["guardian"], {})

    def test_pr_status_exposes_integration_contract_and_live_state(self) -> None:
        pr_body = "\n".join(
            [
                "Issue: #105",
                "item_key: `GOV-0105-integration-governance-baseline`",
                "item_type: `GOV`",
                "release: `governance-baseline`",
                "sprint: `integration-governance`",
                "## integration_check",
                "",
                "- integration_touchpoint: active",
                "- shared_contract_changed: yes",
                "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                "- external_dependency: both",
                "- merge_gate: integration_check_required",
                "- contract_surface: runtime_modes",
                "- joint_acceptance_needed: yes",
                "- integration_status_checked_before_pr: yes",
                "- integration_status_checked_before_merge: no",
            ]
        )
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 105}}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": pr_body},
                    ):
                        with patch("scripts.governance_status.find_latest_guardian_result", return_value={"verdict": "APPROVE", "head_sha": "sha-1"}):
                            with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                with patch(
                                    "scripts.governance_status.load_item_context_from_exec_plan",
                                    return_value={
                                        "Issue": "105",
                                        "item_key": "GOV-0105-integration-governance-baseline",
                                        "item_type": "GOV",
                                        "release": "governance-baseline",
                                        "sprint": "integration-governance",
                                        "exec_plan": "docs/exec-plans/GOV-0105-integration-governance-baseline.md",
                                    },
                                ):
                                    with patch(
                                        "scripts.governance_status.active_exec_plans_for_issue",
                                        return_value=[{"item_key": "GOV-0105-integration-governance-baseline"}],
                                    ):
                                        with patch(
                                            "scripts.governance_status.validate_issue_fetch",
                                            return_value=type(
                                                "Resolution",
                                                (),
                                                {
                                                    "canonical": {
                                                        "integration_touchpoint": "active",
                                                        "shared_contract_changed": "yes",
                                                        "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                                                        "external_dependency": "both",
                                                        "merge_gate": "integration_check_required",
                                                        "contract_surface": "runtime_modes",
                                                        "joint_acceptance_needed": "yes",
                                                    },
                                                    "error": None,
                                                },
                                            )(),
                                        ):
                                            with patch(
                                                "scripts.governance_status.fetch_integration_ref_live_state",
                                                return_value={
                                                    "source": "project_item",
                                                    "status": "review",
                                                    "dependency_order": "parallel",
                                                    "joint_acceptance": "ready",
                                                    "owner_repo": "joint",
                                                    "contract_status": "reviewing",
                                                    "error": "",
                                                },
                                            ) as fetch_live_mock:
                                                payload = governance_status.build_status_payload(pr_number=115)

        self.assertEqual(payload["integration"]["issue_number"], 105)
        self.assertEqual(payload["integration"]["merge_gate"], "integration_check_required")
        self.assertEqual(payload["integration"]["pr_canonical"]["integration_ref"], "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test")
        self.assertEqual(payload["integration"]["integration_ref_live"]["status"], "review")
        fetch_live_mock.assert_called_once_with("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test")

    def test_pr_status_surfaces_live_integration_validation_failures(self) -> None:
        pr_body = "\n".join(
            [
                "Issue: #105",
                "item_key: `GOV-0105-integration-governance-baseline`",
                "item_type: `GOV`",
                "release: `governance-baseline`",
                "sprint: `integration-governance`",
                "## integration_check",
                "",
                "- integration_touchpoint: active",
                "- shared_contract_changed: yes",
                "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                "- external_dependency: both",
                "- merge_gate: integration_check_required",
                "- contract_surface: runtime_modes",
                "- joint_acceptance_needed: yes",
                "- integration_status_checked_before_pr: yes",
                "- integration_status_checked_before_merge: no",
            ]
        )
        resolution = type(
            "Resolution",
            (),
            {
                "canonical": {
                    "integration_touchpoint": "active",
                    "shared_contract_changed": "yes",
                    "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                    "external_dependency": "both",
                    "merge_gate": "integration_check_required",
                    "contract_surface": "runtime_modes",
                    "joint_acceptance_needed": "yes",
                },
                "error": None,
            },
        )()
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 105}}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": pr_body},
                    ):
                        with patch("scripts.governance_status.find_latest_guardian_result", return_value={"verdict": "APPROVE", "head_sha": "sha-1"}):
                            with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                with patch("scripts.governance_status.validate_issue_fetch", return_value=resolution):
                                    with patch(
                                        "scripts.governance_status.fetch_integration_ref_live_state",
                                        return_value={
                                            "source": "project_item",
                                            "status": "review",
                                            "dependency_order": "parallel",
                                            "joint_acceptance": "pending",
                                            "owner_repo": "joint",
                                            "contract_status": "reviewing",
                                            "error": "",
                                        },
                                    ):
                                        payload = governance_status.build_status_payload(pr_number=115)

        self.assertEqual(payload["integration"]["integration_ref_live_errors"], ["`integration_ref` 联合验收状态未就绪（当前 `pending`），拒绝继续。"])
        text_output = governance_status.render_text(payload)
        self.assertIn("integration_ref_live_errors=1", text_output)
        self.assertIn("联合验收状态未就绪", text_output)

    def test_pr_status_without_integration_check_still_surfaces_issue_live_gate_failures(self) -> None:
        pr_body = "\n".join(
            [
                "Issue: #105",
                "item_key: `GOV-0105-integration-governance-baseline`",
                "item_type: `GOV`",
                "release: `governance-baseline`",
                "sprint: `integration-governance`",
            ]
        )
        resolution = type(
            "Resolution",
            (),
            {
                "canonical": {
                    "integration_touchpoint": "active",
                    "shared_contract_changed": "yes",
                    "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                    "external_dependency": "both",
                    "merge_gate": "integration_check_required",
                    "contract_surface": "runtime_modes",
                    "joint_acceptance_needed": "yes",
                },
                "error": None,
            },
        )()
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 105}}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": pr_body},
                    ):
                        with patch("scripts.governance_status.find_latest_guardian_result", return_value={"verdict": "APPROVE", "head_sha": "sha-1"}):
                            with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                with patch("scripts.governance_status.validate_issue_fetch", return_value=resolution):
                                    with patch(
                                        "scripts.governance_status.fetch_integration_ref_live_state",
                                        return_value={
                                            "source": "project_item",
                                            "status": "review",
                                            "dependency_order": "parallel",
                                            "joint_acceptance": "pending",
                                            "owner_repo": "joint",
                                            "contract_status": "reviewing",
                                            "error": "",
                                        },
                                    ):
                                        payload = governance_status.build_status_payload(pr_number=115)

        self.assertEqual(
            payload["integration"]["integration_ref_live_errors"],
            ["`integration_ref` 联合验收状态未就绪（当前 `pending`），拒绝继续。"],
        )
        self.assertTrue(payload["integration"]["comparison_errors"])
        self.assertEqual(payload["integration"]["merge_gate"], "integration_check_required")
        self.assertTrue(payload["integration"]["merge_gate_requires_recheck"])
        text_output = governance_status.render_text(payload)
        self.assertIn("merge_gate=integration_check_required", text_output)

    def test_issue_status_reports_issue_canonical_without_pr_only_errors(self) -> None:
        resolution = type(
            "Resolution",
            (),
            {
                "canonical": {
                    "integration_touchpoint": "active",
                    "shared_contract_changed": "yes",
                    "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                    "external_dependency": "both",
                    "merge_gate": "integration_check_required",
                    "contract_surface": "runtime_modes",
                    "joint_acceptance_needed": "yes",
                },
                "error": None,
            },
        )()
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {}}):
                    with patch("scripts.governance_status.matching_exec_plan_for_issue", return_value={}):
                        with patch("scripts.governance_status.validate_issue_fetch", return_value=resolution):
                            with patch(
                                "scripts.governance_status.fetch_integration_ref_live_state",
                                return_value={
                                    "source": "project_item",
                                    "status": "review",
                                    "dependency_order": "parallel",
                                    "joint_acceptance": "ready",
                                    "owner_repo": "joint",
                                    "contract_status": "reviewing",
                                    "error": "",
                                },
                            ):
                                payload = governance_status.build_status_payload(issue_number=105)

        self.assertEqual(payload["integration"]["issue_number"], 105)
        self.assertEqual(payload["integration"]["pr_canonical"], {})
        self.assertEqual(payload["integration"]["comparison_errors"], [])
        self.assertEqual(payload["integration"]["merge_validation_errors"], [])
        self.assertEqual(payload["integration"]["integration_ref_live_errors"], [])
        self.assertEqual(payload["integration"]["merge_gate"], "integration_check_required")

    def test_pr_body_missing_item_context_fields_returns_empty(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                    with patch("scripts.governance_status.fetch_pr_meta", return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": "item_key: `GOV-0015-item-context-gate`"}):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_requires_worktree_binding(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={
                            "headRefOid": "sha-1",
                            "headRefName": "feature/x",
                            "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                        },
                    ):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            with patch(
                                "scripts.governance_status.load_item_context_from_exec_plan",
                                return_value={
                                    "Issue": "19",
                                    "item_key": "GOV-0015-item-context-gate",
                                    "item_type": "GOV",
                                    "release": "v0.1.0",
                                    "sprint": "2026-S14",
                                    "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
                                },
                            ):
                                with patch(
                                    "scripts.governance_status.active_exec_plans_for_issue",
                                    return_value=[{"item_key": "GOV-0015-item-context-gate"}],
                                ):
                                    payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_rejects_exec_plan_item_key_drift(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={
                            "headRefOid": "sha-1",
                            "headRefName": "feature/x",
                            "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                        },
                    ):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            with patch(
                                "scripts.governance_status.load_item_context_from_exec_plan",
                                return_value={
                                    "Issue": "19",
                                    "item_key": "GOV-0099-drifted",
                                    "item_type": "GOV",
                                    "release": "v0.1.0",
                                    "sprint": "2026-S14",
                                    "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
                                },
                            ):
                                with patch(
                                    "scripts.governance_status.active_exec_plans_for_issue",
                                    return_value=[{"item_key": "GOV-0015-item-context-gate"}],
                                ):
                                    payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_rejects_worktree_issue_mismatch(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 18}}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={
                            "headRefOid": "sha-1",
                            "headRefName": "feature/x",
                            "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                        },
                    ):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            with patch(
                                "scripts.governance_status.load_item_context_from_exec_plan",
                                return_value={
                                    "Issue": "19",
                                    "item_key": "GOV-0015-item-context-gate",
                                    "item_type": "GOV",
                                    "release": "v0.1.0",
                                    "sprint": "2026-S14",
                                    "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
                                },
                            ):
                                payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_without_active_exec_plan_returns_empty_item_context(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                    with patch("scripts.governance_status.fetch_pr_meta", return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": ""}):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            with patch("scripts.governance_status.matching_exec_plan_for_issue", return_value={}):
                                payload = governance_status.build_status_payload(pr_number=7)

        self.assertEqual(payload["item_context"], {})

    def test_issue_status_ignores_inactive_legacy_exec_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "legacy.md").write_text(
                "\n".join(
                    [
                        "# legacy",
                        "",
                        "## 事项上下文",
                        "",
                        "- Issue：`#6`",
                        "- item_key：`FR-0001-governance-stack-v1`",
                        "- item_type：`FR`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S13`",
                        "- 状态：`inactive for PR #15`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with patch("scripts.governance_status.REPO_ROOT", repo):
                payload = governance_status.build_status_payload(issue_number=6)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_ignores_inactive_exec_plan_from_pr_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "GOV-0015-item-context-gate.md").write_text(
                "\n".join(
                    [
                        "# plan",
                        "",
                        "## 关联信息",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "- 状态：`inactive for PR #18`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("scripts.governance_status.REPO_ROOT", repo):
                with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
                    with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                        with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k"}}}):
                            with patch("scripts.governance_status.fetch_pr_meta", return_value={"headRefOid": "sha-1", "headRefName": "feature/x", "body": "item_key: `GOV-0015-item-context-gate`"}):
                                with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                    payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_does_not_fallback_to_other_issue_plan_when_body_item_key_misses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "other-active.md").write_text(
                "\n".join(
                    [
                        "# other",
                        "",
                        "## 关联信息",
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
            with patch("scripts.governance_status.REPO_ROOT", repo):
                with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
                    with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                        with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                            with patch(
                                "scripts.governance_status.fetch_pr_meta",
                                return_value={
                                    "headRefOid": "sha-1",
                                    "headRefName": "feature/x",
                                    "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                                },
                            ):
                                with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                    payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_returns_empty_when_issue_has_multiple_active_exec_plans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            for name, item_key in (
                ("GOV-0015-item-context-gate.md", "GOV-0015-item-context-gate"),
                ("other-active.md", "GOV-0014-release-sprint-structure"),
            ):
                (exec_plans / name).write_text(
                    "\n".join(
                        [
                            "# plan",
                            "",
                            "## 关联信息",
                            "",
                            "- Issue：`#19`",
                            f"- item_key：`{item_key}`",
                            "- item_type：`GOV`",
                            "- release：`v0.1.0`",
                            "- sprint：`2026-S14`",
                            f"- active 收口事项：`{item_key}`",
                            "",
                        ]
                    ),
                    encoding="utf-8",
                )

            with patch("scripts.governance_status.REPO_ROOT", repo):
                with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
                    with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                        with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                            with patch(
                                "scripts.governance_status.fetch_pr_meta",
                                return_value={
                                    "headRefOid": "sha-1",
                                    "headRefName": "feature/x",
                                    "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                                },
                            ):
                                with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                    payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_requires_matching_worktree_path(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch(
                    "scripts.governance_status.load_worktree_state",
                    return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19, "path": "/tmp/other"}}},
                ):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={
                            "headRefOid": "sha-1",
                            "headRefName": "feature/x",
                            "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                        },
                    ):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            with patch(
                                "scripts.governance_status.load_item_context_from_exec_plan",
                                return_value={
                                    "Issue": "19",
                                    "item_key": "GOV-0015-item-context-gate",
                                    "item_type": "GOV",
                                    "release": "v0.1.0",
                                    "sprint": "2026-S14",
                                    "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
                                },
                            ):
                                payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_returns_empty_when_branch_has_multiple_worktree_bindings(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch(
                    "scripts.governance_status.load_worktree_state",
                    return_value={
                        "worktrees": {
                            "k1": {"branch": "feature/x", "key": "k1", "issue": 19, "path": "/tmp/one"},
                            "k2": {"branch": "feature/x", "key": "k2", "issue": 19, "path": "/tmp/two"},
                        }
                    },
                ):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={
                            "headRefOid": "sha-1",
                            "headRefName": "feature/x",
                            "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                        },
                    ):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})
        self.assertEqual(len(payload["worktrees"]), 2)

    def test_pr_status_returns_empty_when_issue_in_body_is_not_numeric(self) -> None:
        with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
            with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k", "issue": 19}}}):
                    with patch(
                        "scripts.governance_status.fetch_pr_meta",
                        return_value={
                            "headRefOid": "sha-1",
                            "headRefName": "feature/x",
                            "body": "Issue: not-a-number\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                        },
                    ):
                        with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                            with patch(
                                "scripts.governance_status.load_item_context_from_exec_plan",
                                return_value={
                                    "Issue": "19",
                                    "item_key": "GOV-0015-item-context-gate",
                                    "item_type": "GOV",
                                    "release": "v0.1.0",
                                    "sprint": "2026-S14",
                                    "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
                                },
                            ):
                                payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_pr_status_rejects_mismatched_active_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "GOV-0015-item-context-gate.md").write_text(
                "\n".join(
                    [
                        "# plan",
                        "",
                        "## 关联信息",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "- active 收口事项：`GOV-0014-release-sprint-structure`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            with patch("scripts.governance_status.REPO_ROOT", repo):
                with patch("scripts.governance_status.load_guardian_state", return_value={"prs": {}}):
                    with patch("scripts.governance_status.load_review_poller_state", return_value={"prs": {}}):
                        with patch("scripts.governance_status.load_worktree_state", return_value={"worktrees": {"k": {"branch": "feature/x", "key": "k"}}}):
                            with patch(
                                "scripts.governance_status.fetch_pr_meta",
                                return_value={
                                    "headRefOid": "sha-1",
                                    "headRefName": "feature/x",
                                    "body": "Issue: #19\nitem_key: `GOV-0015-item-context-gate`\nitem_type: `GOV`\nrelease: `v0.1.0`\nsprint: `2026-S14`\n",
                                },
                            ):
                                with patch("scripts.governance_status.fetch_checks_summary", return_value=[]):
                                    payload = governance_status.build_status_payload(pr_number=20)

        self.assertEqual(payload["item_context"], {})

    def test_issue_status_rejects_mismatched_active_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "GOV-0015-item-context-gate.md").write_text(
                "\n".join(
                    [
                        "# plan",
                        "",
                        "## 关联信息",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- item_type：`GOV`",
                        "- release：`v0.1.0`",
                        "- sprint：`2026-S14`",
                        "- active 收口事项：`GOV-0014-release-sprint-structure`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with patch("scripts.governance_status.REPO_ROOT", repo):
                payload = governance_status.build_status_payload(issue_number=19)

        self.assertEqual(payload["item_context"], {})

    def test_issue_status_returns_empty_when_multiple_non_inactive_exec_plans_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            for name, item_key in (
                ("one.md", "GOV-0015-item-context-gate"),
                ("two.md", "GOV-0014-release-sprint-structure"),
            ):
                (exec_plans / name).write_text(
                    "\n".join(
                        [
                            "# plan",
                            "",
                            "## 关联信息",
                            "",
                            "- Issue：`#19`",
                            f"- item_key：`{item_key}`",
                            "- item_type：`GOV`",
                            "- release：`v0.1.0`",
                            "- sprint：`2026-S14`",
                            "",
                        ]
                    ),
                    encoding="utf-8",
                )

            with patch("scripts.governance_status.REPO_ROOT", repo):
                payload = governance_status.build_status_payload(issue_number=19)

        self.assertEqual(payload["item_context"], {})

    def test_issue_status_ignores_incomplete_exec_plan_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            exec_plans = repo / "docs" / "exec-plans"
            exec_plans.mkdir(parents=True, exist_ok=True)
            (exec_plans / "broken.md").write_text(
                "\n".join(
                    [
                        "# broken",
                        "",
                        "## 关联信息",
                        "",
                        "- Issue：`#19`",
                        "- item_key：`GOV-0015-item-context-gate`",
                        "- item_type：`GOV`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with patch("scripts.governance_status.REPO_ROOT", repo):
                payload = governance_status.build_status_payload(issue_number=19)

        self.assertEqual(payload["item_context"], {})

    def test_load_state_with_legacy_reads_legacy_when_primary_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            primary = root / "new.json"
            legacy = root / "legacy.json"
            legacy.write_text(json.dumps({"prs": {"1": {"head_sha": "legacy-sha"}}}), encoding="utf-8")

            payload = governance_status.load_state_with_legacy(primary, legacy)

        self.assertIn("prs", payload)
        self.assertEqual(payload["prs"]["1"]["head_sha"], "legacy-sha")

    def test_text_and_json_outputs_are_consistent(self) -> None:
        sample = {
            "guardian": {"verdict": "APPROVE", "safe_to_merge": True, "head_sha": "sha-x", "reviewed_at": "2026-03-29T10:00:00Z"},
            "review_poller": {"head_sha": "sha-x", "reviewed_at": "2026-03-29T10:00:01Z"},
            "worktrees": [{"key": "issue-1-demo", "branch": "issue-1-demo", "path": "/tmp/demo"}],
            "item_context": {
                "Issue": "19",
                "item_key": "GOV-0015-item-context-gate",
                "item_type": "GOV",
                "release": "v0.1.0",
                "sprint": "2026-S14",
                "exec_plan": "docs/exec-plans/GOV-0015-item-context-gate.md",
            },
            "checks": [{"name": "Validate Governance Tooling", "bucket": "pass", "state": "SUCCESS"}],
        }

        text_output = governance_status.render_text(sample)
        json_output = json.loads(json.dumps(sample, ensure_ascii=False))

        self.assertIn("verdict=APPROVE", text_output)
        self.assertIn("count=1", text_output)
        self.assertIn("item_key=GOV-0015-item-context-gate", text_output)
        self.assertEqual(json_output["guardian"]["head_sha"], "sha-x")
        self.assertEqual(len(json_output["worktrees"]), 1)


if __name__ == "__main__":
    unittest.main()
