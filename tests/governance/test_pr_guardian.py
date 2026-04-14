from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from scripts.common import CommandError
from scripts.pr_guardian import (
    build_item_context_summary,
    build_prompt,
    build_review_context,
    codex_review_timeout_seconds,
    extract_reviewer_rubric_excerpt,
    fetch_issue_context,
    find_latest_guardian_result,
    integration_merge_gate_errors,
    load_guardian_state,
    load_reviewer_rubric_excerpt,
    merge_if_safe,
    parse_bullet_kv_section,
    parse_integration_check_payload,
    guardian_body_fingerprint,
    integration_status_checked_before_merge_value,
    render_item_context_supplement,
    review_once,
    run_codex_review,
    save_guardian_result,
    set_integration_status_checked_before_merge,
)


LOCAL_ONLY_INTEGRATION_CHECK_BODY = "\n".join(
    [
        "## integration_check",
        "",
        "- integration_touchpoint: none",
        "- shared_contract_changed: no",
        "- integration_ref: none",
        "- external_dependency: none",
        "- merge_gate: local_only",
        "- contract_surface: none",
        "- joint_acceptance_needed: no",
        "- integration_status_checked_before_pr: no",
        "- integration_status_checked_before_merge: no",
    ]
)

CONTRADICTORY_LOCAL_ONLY_INTEGRATION_CHECK_BODY = "\n".join(
    [
        "## integration_check",
        "",
        "- integration_touchpoint: active",
        "- shared_contract_changed: no",
        "- integration_ref: https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
        "- external_dependency: both",
        "- merge_gate: local_only",
        "- contract_surface: runtime_modes",
        "- joint_acceptance_needed: yes",
        "- integration_status_checked_before_pr: yes",
        "- integration_status_checked_before_merge: yes",
    ]
)

INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY = "\n".join(
    [
        "## integration_check",
        "",
        "- integration_touchpoint: active",
        "- shared_contract_changed: no",
        "- integration_ref: https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
        "- external_dependency: both",
        "- merge_gate: integration_check_required",
        "- contract_surface: runtime_modes",
        "- joint_acceptance_needed: yes",
        "- integration_status_checked_before_pr: yes",
        "- integration_status_checked_before_merge: no",
        "",
        "补充说明：",
        "",
        "- merge 前仍需再次核对 integration 状态",
    ]
)


def cached_guardian_result(head_sha: str, body: str, *, verdict: str = "APPROVE", safe_to_merge: bool = True, summary: str = "cached") -> dict[str, object]:
    return {
        "schema_version": 2,
        "pr_number": 1,
        "head_sha": head_sha,
        "body_fingerprint": guardian_body_fingerprint(body),
        "verdict": verdict,
        "safe_to_merge": safe_to_merge,
        "summary": summary,
        "reviewed_at": "2026-03-28T10:00:00Z",
    }


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

    def test_find_latest_guardian_result_accepts_schema_v1_when_body_is_provided(self) -> None:
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

            payload = find_latest_guardian_result(
                1,
                "sha-1",
                body="## integration_check\n\n- integration_status_checked_before_pr: yes\n",
                path=state_path,
            )

            self.assertIsNotNone(payload)
            self.assertEqual(payload["head_sha"], "sha-1")

    def test_find_latest_guardian_result_rejects_schema_v1_when_body_bound_is_required(self) -> None:
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

            payload = find_latest_guardian_result(
                1,
                "sha-1",
                body="## integration_check\n\n- integration_status_checked_before_pr: yes\n",
                require_body_bound=True,
                path=state_path,
            )

            self.assertIsNone(payload)

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

    def test_find_latest_guardian_result_rejects_body_drift_with_same_head(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "guardian.json"
            reviewed_body = "## integration_check\n\n- integration_status_checked_before_pr: yes\n"
            save_guardian_result(
                1,
                {
                    "schema_version": 2,
                    "pr_number": 1,
                    "head_sha": "sha-1",
                    "body_fingerprint": guardian_body_fingerprint(reviewed_body),
                    "verdict": "APPROVE",
                    "safe_to_merge": True,
                    "summary": "cached",
                    "reviewed_at": "2026-03-28T10:00:00Z",
                },
                path=state_path,
            )

            payload = find_latest_guardian_result(
                1,
                "sha-1",
                body=reviewed_body + "\n补充说明：body changed\n",
                path=state_path,
            )

            self.assertIsNone(payload)


class CodexReviewExecutionTests(unittest.TestCase):
    def test_set_integration_status_checked_before_merge_updates_only_integration_check_section(self) -> None:
        body = "\n".join(
            [
                "## 摘要",
                "",
                "- integration_status_checked_before_merge: no",
                "",
                "## integration_check",
                "",
                "- integration_touchpoint: active",
                "- shared_contract_changed: no",
                "- integration_ref: https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "- external_dependency: both",
                "- merge_gate: integration_check_required",
                "- contract_surface: runtime_modes",
                "- joint_acceptance_needed: yes",
                "- integration_status_checked_before_pr: yes",
                "- integration_status_checked_before_merge: no",
            ]
        )

        updated = set_integration_status_checked_before_merge(body, "yes")

        self.assertIn("## 摘要\n\n- integration_status_checked_before_merge: no", updated)
        self.assertIn("## integration_check", updated)
        self.assertIn("- integration_status_checked_before_merge: yes", updated)
        self.assertEqual(integration_status_checked_before_merge_value(updated), "yes")

    def test_merge_recheck_reader_ignores_same_named_bullet_outside_integration_check_section(self) -> None:
        body = "\n".join(
            [
                "## 补充说明",
                "",
                "- integration_status_checked_before_merge: yes",
                "",
                "## integration_check",
                "",
                "- integration_touchpoint: active",
                "- shared_contract_changed: no",
                "- integration_ref: https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "- external_dependency: both",
                "- merge_gate: integration_check_required",
                "- contract_surface: runtime_modes",
                "- joint_acceptance_needed: yes",
                "- integration_status_checked_before_pr: yes",
                "- integration_status_checked_before_merge: no",
            ]
        )

        self.assertEqual(integration_status_checked_before_merge_value(body), "no")

    def test_parse_bullet_kv_section_ignores_following_explanatory_heading(self) -> None:
        section = "\n".join(
            [
                "- integration_touchpoint: active",
                "- shared_contract_changed: no",
                "- integration_ref:",
                "  https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "- external_dependency: both",
                "- merge_gate: integration_check_required",
                "- contract_surface: runtime_modes",
                "- joint_acceptance_needed: yes",
                "- integration_status_checked_before_pr: yes",
                "- integration_status_checked_before_merge: yes",
                "",
                "补充说明：",
                "",
                "- merge 前必须再次核对 integration 状态",
            ]
        )

        payload = parse_bullet_kv_section(section)

        self.assertEqual(payload["integration_status_checked_before_merge"], "yes")
        self.assertEqual(payload["integration_ref"], "https://github.com/MC-and-his-Agents/WebEnvoy/issues/466")

    def test_parse_integration_check_payload_ignores_free_form_note_bullets(self) -> None:
        section = "\n".join(
            [
                "- integration_touchpoint: active",
                "- shared_contract_changed: no",
                "- integration_ref: https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                "- external_dependency: both",
                "- merge_gate: integration_check_required",
                "- contract_surface: runtime_modes",
                "- joint_acceptance_needed: yes",
                "- integration_status_checked_before_pr: yes",
                "- integration_status_checked_before_merge: no",
                "",
                "补充说明：",
                "",
                "- integration_status_checked_before_merge: yes",
            ]
        )

        payload = parse_integration_check_payload(section)

        self.assertEqual(payload["integration_status_checked_before_merge"], "no")

    def test_integration_merge_gate_errors_accepts_standard_template_shape(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref:",
                    "  https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                    "",
                    "补充说明：",
                    "",
                    "- merge 前必须再次核对 integration 状态",
                ]
            )
        }

        self.assertEqual(integration_merge_gate_errors(meta), [])

    @patch(
        "scripts.pr_guardian.fetch_integration_ref_live_state",
        return_value={
            "source": "project_item",
            "status": "blocked",
            "dependency_order": "parallel",
            "joint_acceptance": "ready",
            "blocked": True,
            "error": "",
        },
    )
    def test_integration_merge_gate_errors_require_live_state_blocks_blocked_integration_ref(self, live_state_mock) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta, require_live_state=True)

        self.assertTrue(any("blocked" in item for item in errors))
        live_state_mock.assert_called_once()

    @patch(
        "scripts.pr_guardian.fetch_integration_ref_live_state",
        return_value={
            "source": "project_item",
            "error": "无法读取 `integration_ref` 指向的 project item `PVTI_test`，拒绝继续。",
        },
    )
    def test_integration_merge_gate_errors_require_live_state_fail_closed_when_ref_unreadable(self, live_state_mock) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta, require_live_state=True)

        self.assertEqual(errors, ["无法读取 `integration_ref` 指向的 project item `PVTI_test`，拒绝继续。"])
        live_state_mock.assert_called_once()

    @patch(
        "scripts.pr_guardian.fetch_integration_ref_live_state",
        return_value={
            "source": "project_item",
            "status": "review",
            "dependency_order": "parallel",
            "joint_acceptance": "ready",
            "owner_repo": "joint",
            "contract_status": "reviewing",
            "blocked": False,
            "error": "",
        },
    )
    def test_integration_merge_gate_errors_require_live_state_passes_when_ref_ready(self, live_state_mock) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta, require_live_state=True)

        self.assertEqual(errors, [])
        live_state_mock.assert_called_once()

    @patch(
        "scripts.pr_guardian.fetch_integration_ref_live_state",
        return_value={
            "source": "project_item",
            "status": "in_progress",
            "dependency_order": "parallel",
            "joint_acceptance": "ready",
            "owner_repo": "joint",
            "contract_status": "reviewing",
            "blocked": False,
            "error": "",
        },
    )
    def test_integration_merge_gate_errors_require_live_state_rejects_in_progress_status(self, live_state_mock) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta, require_live_state=True)

        self.assertTrue(any("未进入允许合并的状态集合" in item for item in errors))
        live_state_mock.assert_called_once()

    def test_integration_merge_gate_errors_allows_missing_section_for_legacy_pr(self) -> None:
        meta = {"body": "## 摘要\n\n- 变更目的：补齐 integration gate\n"}

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(errors, [])

    @patch("scripts.pr_guardian.resolve_issue_canonical_integration", return_value=(105, {"merge_gate": "integration_check_required"}))
    def test_integration_merge_gate_errors_rejects_missing_section_when_issue_declares_canonical_metadata(self, resolve_issue_mock) -> None:
        meta = {"body": "## 摘要\n\n- 变更目的：补齐 integration gate\n"}

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(errors, ["PR 对应的 Issue #105 已声明 canonical integration 元数据，PR 描述缺少 canonical `integration_check` 段落。"])
        resolve_issue_mock.assert_called_once_with(meta)

    @patch("scripts.pr_guardian.resolve_issue_canonical_integration", return_value=(105, {}))
    def test_integration_merge_gate_errors_allows_legacy_issue_without_canonical_metadata(self, resolve_issue_mock) -> None:
        meta = {"body": "## 摘要\n\n- 变更目的：补齐 integration gate\n"}

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(errors, [])
        resolve_issue_mock.assert_called_once_with(meta)

    def test_integration_merge_gate_errors_rejects_issue_canonical_lookup_failure(self) -> None:
        meta = {"body": "## 摘要\n\n- 变更目的：补齐 integration gate\n"}

        def resolve_side_effect(payload):
            payload["_issue_canonical_integration_error"] = "无法读取 Issue #105 的 canonical integration 元数据，拒绝继续。"
            return 105, {}

        with patch("scripts.pr_guardian.resolve_issue_canonical_integration", side_effect=resolve_side_effect) as resolve_issue_mock:
            errors = integration_merge_gate_errors(meta)

        self.assertEqual(errors, ["无法读取 Issue #105 的 canonical integration 元数据，拒绝继续。"])
        resolve_issue_mock.assert_called_once_with(meta)

    def test_integration_merge_gate_errors_rejects_missing_canonical_fields(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- integration_ref: #12",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: no",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(
            errors,
            [
                "PR 描述中的 `integration_check` 缺少必填字段："
                "`integration_check.joint_acceptance_needed`、`integration_check.shared_contract_changed`。"
            ],
        )

    def test_integration_merge_gate_errors_rejects_unknown_merge_gate_value(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- merge_gate: experimental_mode",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(
            errors,
            ["PR 描述中的 `integration_check.merge_gate` 非法：`experimental_mode`（仅允许 `local_only` / `integration_check_required`）。"],
        )

    def test_integration_merge_gate_errors_requires_metadata_for_required_gate(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: none",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: no",
                    "- integration_status_checked_before_merge: no",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertIn("`merge_gate=integration_check_required` 时，`integration_ref` 必须指向具体 integration issue / item。", errors)
        self.assertIn("`merge_gate=integration_check_required` 时，PR 描述必须记录 `integration_status_checked_before_pr=yes`。", errors)
        self.assertIn(
            "`merge_gate=integration_check_required` 时，进入 `merge_pr` 前必须把 `integration_status_checked_before_merge` 更新为 `yes`。",
            errors,
        )

    def test_integration_merge_gate_errors_rejects_local_only_with_integration_invariants(self) -> None:
        meta = {"body": CONTRADICTORY_LOCAL_ONLY_INTEGRATION_CHECK_BODY}

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(
            errors,
            [
                "`merge_gate=local_only` 与当前 integration 元数据冲突："
                "当 `integration_touchpoint != none`、`shared_contract_changed=yes`、`external_dependency != none`、"
                "`contract_surface != none` 或 `joint_acceptance_needed=yes` 时，"
                "`merge_gate` 必须为 `integration_check_required`。"
            ],
        )

    def test_integration_merge_gate_errors_rejects_invalid_enum_values(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: unexpected",
                    "- shared_contract_changed: maybe",
                    "- integration_ref: #12",
                    "- external_dependency: somewhere",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: typo_surface",
                    "- joint_acceptance_needed: maybe",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertTrue(any("integration_touchpoint" in error for error in errors))
        self.assertTrue(any("shared_contract_changed" in error for error in errors))
        self.assertTrue(any("external_dependency" in error for error in errors))
        self.assertTrue(any("contract_surface" in error for error in errors))
        self.assertTrue(any("joint_acceptance_needed" in error for error in errors))

    def test_integration_merge_gate_errors_rejects_invalid_status_enum_values(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: none",
                    "- shared_contract_changed: no",
                    "- integration_ref: none",
                    "- external_dependency: none",
                    "- merge_gate: local_only",
                    "- contract_surface: none",
                    "- joint_acceptance_needed: no",
                    "- integration_status_checked_before_pr: later",
                    "- integration_status_checked_before_merge: maybe",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertTrue(any("integration_status_checked_before_pr" in error for error in errors))
        self.assertTrue(any("integration_status_checked_before_merge" in error for error in errors))

    @patch(
        "scripts.pr_guardian.resolve_issue_canonical_integration",
        return_value=(
            105,
            {
                "integration_touchpoint": "active",
                "shared_contract_changed": "yes",
                "integration_ref": "owner/repo#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
        ),
    )
    def test_integration_merge_gate_errors_rejects_pr_issue_canonical_mismatch(self, resolve_issue_mock) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: owner/repo#12",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertIn("`integration_check.shared_contract_changed` 与 Issue #105 中的 canonical integration 元数据不一致。", errors)
        resolve_issue_mock.assert_called_once_with(meta)

    def test_integration_merge_gate_errors_rejects_uncheckable_integration_ref(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: later",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertTrue(any("可核查的具体 integration issue / item" in error for error in errors))

    def test_integration_merge_gate_errors_accepts_project_item_url_with_view(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=123456",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(errors, [])

    @patch(
        "scripts.pr_guardian.resolve_issue_canonical_integration",
        return_value=(
            105,
            {
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "MC-and-his-Agents/Syvert#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
        ),
    )
    def test_integration_merge_gate_errors_accepts_equivalent_issue_ref_forms(self, resolve_issue_mock) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/MC-and-his-Agents/Syvert/issues/12",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(errors, [])
        resolve_issue_mock.assert_called_once_with(meta)

    @patch(
        "scripts.pr_guardian.resolve_issue_canonical_integration",
        return_value=(
            105,
            {
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?itemId=PVTI_test&pane=issue",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
        ),
    )
    def test_integration_merge_gate_errors_accepts_equivalent_project_item_urls(self, resolve_issue_mock) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(errors, [])
        resolve_issue_mock.assert_called_once_with(meta)

    @patch(
        "scripts.integration_contract.fetch_integration_ref_live_state",
        side_effect=[
            {"item_id": "PVTI_same", "organization": "mc-and-his-agents", "project_number": "3", "error": ""},
            {"item_id": "PVTI_same", "organization": "mc-and-his-agents", "project_number": "3", "error": ""},
        ],
    )
    @patch(
        "scripts.pr_guardian.resolve_issue_canonical_integration",
        return_value=(
            105,
            {
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "MC-and-his-Agents/Syvert#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
        ),
    )
    def test_integration_merge_gate_errors_rejects_cross_form_issue_and_project_item_refs(
        self,
        resolve_issue_mock,
        fetch_live_mock,
    ) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_same",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertEqual(
            errors,
            ["`integration_check.integration_ref` 与 Issue #105 中的 canonical integration 元数据不一致。"],
        )
        resolve_issue_mock.assert_called_once_with(meta)
        fetch_live_mock.assert_not_called()

    def test_integration_merge_gate_errors_rejects_local_only_external_integration_ref(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: none",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
                    "- external_dependency: none",
                    "- merge_gate: local_only",
                    "- contract_surface: none",
                    "- joint_acceptance_needed: no",
                    "- integration_status_checked_before_pr: no",
                    "- integration_status_checked_before_merge: no",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertIn("纯本仓库事项必须显式使用 `integration_ref=none`，不得保留外部 integration 绑定。", errors)

    def test_integration_merge_gate_errors_rejects_local_only_shared_contract_change(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: none",
                    "- shared_contract_changed: yes",
                    "- integration_ref: none",
                    "- external_dependency: none",
                    "- merge_gate: local_only",
                    "- contract_surface: none",
                    "- joint_acceptance_needed: no",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: no",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertTrue(any("shared_contract_changed=yes" in error for error in errors))

    @patch(
        "scripts.pr_guardian.resolve_issue_canonical_integration",
        return_value=(
            105,
            {
                "integration_touchpoint": "active",
                "shared_contract_changed": "yes",
                "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
        ),
    )
    def test_integration_merge_gate_errors_rejects_local_only_issue_canonical_mismatch(self, resolve_issue_mock) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: none",
                    "- shared_contract_changed: no",
                    "- integration_ref: none",
                    "- external_dependency: none",
                    "- merge_gate: local_only",
                    "- contract_surface: none",
                    "- joint_acceptance_needed: no",
                    "- integration_status_checked_before_pr: no",
                    "- integration_status_checked_before_merge: no",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertIn("`integration_check.integration_touchpoint` 与 Issue #105 中的 canonical integration 元数据不一致。", errors)
        self.assertIn("`integration_check.merge_gate` 与 Issue #105 中的 canonical integration 元数据不一致。", errors)
        resolve_issue_mock.assert_called_once_with(meta)

    def test_integration_merge_gate_errors_rejects_required_gate_with_touchpoint_none(self) -> None:
        meta = {
            "body": "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: none",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: yes",
                ]
            )
        }

        errors = integration_merge_gate_errors(meta)

        self.assertIn("`merge_gate=integration_check_required` 时，`integration_touchpoint` 不能为 `none`。", errors)

    @patch("scripts.pr_guardian.subprocess.run")
    def test_run_codex_review_falls_back_to_stdout_json(self, subprocess_run_mock) -> None:
        subprocess_run_mock.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"verdict":"APPROVE","safe_to_merge":true,"summary":"ok","findings":[],"required_actions":[]}',
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict("scripts.pr_guardian.os.environ", {}, clear=True):
                result = run_codex_review(Path(temp_dir), "prompt", Path(temp_dir) / "review.json")

        self.assertEqual(result["verdict"], "APPROVE")
        self.assertTrue(result["safe_to_merge"])
        command = subprocess_run_mock.call_args.args[0]
        self.assertIn("workspace-write", command)
        env = subprocess_run_mock.call_args.kwargs["env"]
        self.assertTrue(env["TMPDIR"].endswith(".codex-tmp"))
        self.assertIsNone(subprocess_run_mock.call_args.kwargs["timeout"])

    @patch("scripts.pr_guardian.subprocess.run")
    def test_run_codex_review_passes_configured_timeout(self, subprocess_run_mock) -> None:
        subprocess_run_mock.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"verdict":"APPROVE","safe_to_merge":true,"summary":"ok","findings":[],"required_actions":[]}',
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict("scripts.pr_guardian.os.environ", {"SYVERT_GUARDIAN_TIMEOUT_SECONDS": "600"}, clear=True):
                run_codex_review(Path(temp_dir), "prompt", Path(temp_dir) / "review.json")

        self.assertEqual(subprocess_run_mock.call_args.kwargs["timeout"], 600)

    @patch("scripts.pr_guardian.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["codex"], timeout=300))
    def test_run_codex_review_times_out_with_actionable_error(self, subprocess_run_mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict("scripts.pr_guardian.os.environ", {"SYVERT_GUARDIAN_TIMEOUT_SECONDS": "300"}, clear=False):
                with self.assertRaises(SystemExit) as ctx:
                    run_codex_review(Path(temp_dir), "prompt", Path(temp_dir) / "review.json")

        self.assertIn("Codex 审查超时（>300 秒）", str(ctx.exception))
        self.assertEqual(subprocess_run_mock.call_args.kwargs["timeout"], 300)
        subprocess_run_mock.assert_called_once()

    def test_codex_review_timeout_seconds_defaults_to_none(self) -> None:
        with patch.dict("scripts.pr_guardian.os.environ", {}, clear=True):
            self.assertIsNone(codex_review_timeout_seconds())

    def test_codex_review_timeout_seconds_accepts_positive_integer(self) -> None:
        with patch.dict("scripts.pr_guardian.os.environ", {"SYVERT_GUARDIAN_TIMEOUT_SECONDS": "600"}, clear=True):
            self.assertEqual(codex_review_timeout_seconds(), 600)

    def test_codex_review_timeout_seconds_rejects_zero(self) -> None:
        with patch.dict("scripts.pr_guardian.os.environ", {"SYVERT_GUARDIAN_TIMEOUT_SECONDS": "0"}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                codex_review_timeout_seconds()

        self.assertIn("SYVERT_GUARDIAN_TIMEOUT_SECONDS", str(ctx.exception))

    def test_codex_review_timeout_seconds_rejects_negative_integer(self) -> None:
        with patch.dict("scripts.pr_guardian.os.environ", {"SYVERT_GUARDIAN_TIMEOUT_SECONDS": "-1"}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                codex_review_timeout_seconds()

        self.assertIn("SYVERT_GUARDIAN_TIMEOUT_SECONDS", str(ctx.exception))

    def test_codex_review_timeout_seconds_rejects_invalid_value(self) -> None:
        with patch.dict("scripts.pr_guardian.os.environ", {"SYVERT_GUARDIAN_TIMEOUT_SECONDS": "abc"}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                codex_review_timeout_seconds()

        self.assertIn("SYVERT_GUARDIAN_TIMEOUT_SECONDS", str(ctx.exception))

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
                    "summary": "",
                },
                "item_context": {"issue": "24", "item_key": "GOV-0024-guardian-review-context"},
                "raw_sections": {
                    "Issue 摘要": "## Goal\n\n- 精简 review context",
                    "摘要": "- 变更目的：精简 prompt",
                    "关联事项": "- Issue: #24\n- Closing: Fixes #24",
                    "风险级别": "- `medium`",
                    "验证": "- python3 -m unittest",
                    "回滚": "- revert PR",
                    "检查清单": "- [x] 已填写 Closing",
                },
                "pr_sections": {
                    "issue_summary": "## Goal\n\n- 精简 review context",
                    "item_context": "- Issue: #24\n- Closing: Fixes #24",
                    "summary": "- 变更目的：精简 prompt",
                    "risk": "- `medium`",
                    "validation": "- python3 -m unittest",
                    "rollback": "- revert PR",
                },
                "integration_review_packet": {
                    "contract_sources": [
                        "scripts/policy/integration_contract.json",
                        "scripts/integration_contract.py",
                    ],
                    "issue_number": 24,
                    "issue_error": "",
                    "issue_canonical": {
                        "integration_touchpoint": "active",
                        "shared_contract_changed": "no",
                        "integration_ref": "#24",
                        "external_dependency": "both",
                        "merge_gate": "integration_check_required",
                        "contract_surface": "runtime_modes",
                        "joint_acceptance_needed": "yes",
                    },
                    "normalized_issue_canonical": {
                        "integration_ref": "issue:mc-and-his-agents/syvert#24",
                    },
                    "pr_canonical": {
                        "integration_touchpoint": "active",
                        "shared_contract_changed": "no",
                        "integration_ref": "https://github.com/MC-and-his-Agents/Syvert/issues/24",
                        "external_dependency": "both",
                        "merge_gate": "integration_check_required",
                        "contract_surface": "runtime_modes",
                        "joint_acceptance_needed": "yes",
                        "integration_status_checked_before_pr": "yes",
                        "integration_status_checked_before_merge": "no",
                    },
                    "normalized_pr_canonical": {
                        "integration_ref": "issue:mc-and-his-agents/syvert#24",
                    },
                    "comparison_errors": [],
                    "merge_gate": "integration_check_required",
                    "merge_gate_requires_recheck": True,
                    "merge_validation_errors": [
                        "`merge_gate=integration_check_required` 时，进入 `merge_pr` 前必须把 `integration_status_checked_before_merge` 更新为 `yes`。"
                    ],
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
        self.assertIn("PR 关联事项补充：\n- Closing: Fixes #24", prompt)
        self.assertIn("Diff Stat：", prompt)
        self.assertIn("docs/exec-plans/GOV-0024-guardian-review-context.md", prompt)
        self.assertIn("## Review Rubric", prompt)
        self.assertIn("Integration Review Packet：", prompt)
        self.assertIn("normalized_issue_canonical", prompt)
        self.assertIn("integration_status_checked_before_merge", prompt)
        self.assertNotIn("PR 正文 fallback：", prompt)
        self.assertNotIn("审查输入", prompt)
        self.assertNotIn("进入 `merge-ready` 前，必须同时满足", prompt)
        self.assertNotIn("默认 Squash Merge", prompt)
        self.assertNotIn("检查清单：", prompt)

    def test_build_prompt_surfaces_missing_pr_integration_check_as_blocking_packet_error(self) -> None:
        meta = {
            "number": 107,
            "title": "治理: 统一 canonical integration contract",
            "url": "https://example.test/pr/107",
            "baseRefName": "main",
            "headRefOid": "sha-107",
            "headRefName": "issue-105-integration-governance-baseline",
            "body": "## 摘要\n\n- 变更目的：统一 contract\n",
        }

        expected_error = "PR 对应的 Issue #105 已声明 canonical integration 元数据，PR 描述缺少 canonical `integration_check` 段落。"

        with patch(
            "scripts.pr_guardian.build_review_context",
            return_value={
                "pr_identity": ["- PR: #107", "- 标题: 治理: 统一 canonical integration contract"],
                "issue_context": {
                    "identity": ["- Issue: #105", "- 标题: governance: canonical integration contract"],
                    "summary": "",
                },
                "item_context": {"issue": "105", "item_key": "GOV-0105-integration-governance-baseline"},
                "raw_sections": {"摘要": "- 变更目的：统一 contract"},
                "pr_sections": {"summary": "- 变更目的：统一 contract"},
                "integration_review_packet": {
                    "contract_sources": [
                        "scripts/policy/integration_contract.json",
                        "scripts/integration_contract.py",
                    ],
                    "issue_number": 105,
                    "issue_error": "",
                    "issue_canonical": {
                        "integration_touchpoint": "active",
                        "shared_contract_changed": "no",
                        "integration_ref": "#12",
                        "external_dependency": "both",
                        "merge_gate": "integration_check_required",
                        "contract_surface": "runtime_modes",
                        "joint_acceptance_needed": "yes",
                    },
                    "normalized_issue_canonical": {
                        "integration_ref": "issue:mc-and-his-agents/syvert#12",
                    },
                    "pr_canonical": {},
                    "normalized_pr_canonical": {},
                    "comparison_errors": [expected_error],
                    "merge_gate": "none",
                    "merge_gate_requires_recheck": False,
                    "merge_validation_errors": [expected_error],
                },
                "checks": ["- governance: bucket=pass, state=SUCCESS"],
                "worktree_binding": [{"key": "issue-105", "path": "/tmp/issue-105"}],
                "changed_files": ["scripts/integration_contract.py"],
                "diff_stat": "1 file changed, 10 insertions(+), 2 deletions(-)",
                "related_paths": ["docs/exec-plans/GOV-0105-integration-governance-baseline.md"],
                "context_notes": ["结构化事项上下文已加载。"],
            },
        ):
            with patch("scripts.pr_guardian.load_reviewer_rubric_excerpt", return_value="## Review Rubric\n- contract 一致性"):
                prompt = build_prompt(meta, Path("/tmp/worktree"))

        self.assertIn(expected_error, prompt)
        self.assertNotIn("canonical_mismatches: none", prompt)
        self.assertNotIn("merge_gate_validation: ok", prompt)

    def test_extract_reviewer_rubric_excerpt_excludes_review_inputs_section(self) -> None:
        excerpt = extract_reviewer_rubric_excerpt(
            "\n".join(
                [
                    "## 审查输入",
                    "- 当前 PR",
                    "",
                    "## 工件完整性检查",
                    "- 输入齐备",
                    "",
                    "## Review Rubric",
                    "- 行为正确性",
                    "",
                    "## 职责边界说明",
                    "- guardian 负责 merge gate",
                ]
            )
        )

        self.assertNotIn("## 审查输入", excerpt)
        self.assertIn("## 工件完整性检查", excerpt)
        self.assertIn("## Review Rubric", excerpt)
        self.assertIn("## 职责边界说明", excerpt)

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

    def test_build_prompt_omits_only_nonessential_empty_sections(self) -> None:
        meta = {
            "number": 30,
            "title": "治理: 收口 review 治理主题剩余优化",
            "url": "https://example.test/pr/30",
            "baseRefName": "main",
            "headRefOid": "sha-30",
            "headRefName": "issue-30-branch",
            "body": "## 摘要\n\n- 变更目的：收口\n",
        }

        with patch(
            "scripts.pr_guardian.build_review_context",
            return_value={
                "pr_identity": ["- PR: #30"],
                "issue_context": {"identity": [], "summary": ""},
                "item_context": {"issue": "30", "item_key": "GOV-0030-closeout"},
                "raw_sections": {"摘要": "- 变更目的：收口"},
                "pr_sections": {"summary": "- 变更目的：收口"},
                "changed_files": ["code_review.md"],
                "diff_stat": "1 file changed",
                "related_paths": [],
                "context_notes": [],
            },
        ):
            with patch("scripts.pr_guardian.load_reviewer_rubric_excerpt", return_value="## Review Rubric\n- 行为正确性"):
                prompt = build_prompt(meta, Path("/tmp/worktree"))

        self.assertIn("PR 摘要：", prompt)
        self.assertNotIn("PR 关联事项补充：", prompt)
        self.assertIn("风险摘要：", prompt)
        self.assertIn("未提供结构化风险摘要。", prompt)
        self.assertIn("验证摘要：", prompt)
        self.assertIn("未提供结构化验证摘要。", prompt)
        self.assertIn("回滚摘要：", prompt)
        self.assertIn("未提供结构化回滚摘要。", prompt)
        self.assertIn("相关工件路径：", prompt)
        self.assertIn("未直接定位到相关 spec / exec-plan / decision 工件。", prompt)
        self.assertNotIn("Context Notes：", prompt)

    def test_build_prompt_filters_deprecated_template_noise_from_raw_fallback(self) -> None:
        meta = {
            "number": 25,
            "title": "治理: 对齐 review template",
            "url": "https://example.test/pr/25",
            "baseRefName": "main",
            "headRefOid": "sha-25",
            "headRefName": "issue-25-branch",
            "body": "\n".join(
                [
                    "## 摘要",
                    "",
                    "- 变更目的：精简模板",
                    "",
                    "## 检查清单",
                    "",
                    "- [x] 旧模板字段",
                    "",
                    "## 自定义说明",
                    "",
                    "- 只保留 reviewer 需要的补充说明",
                ]
            ),
        }

        with patch(
            "scripts.pr_guardian.build_review_context",
            return_value={
                "pr_identity": ["- PR: #25"],
                "issue_context": {"identity": [], "summary": ""},
                "item_context": {"issue": "25"},
                "raw_sections": {
                    "摘要": "- 变更目的：精简模板",
                    "检查清单": "- [x] 旧模板字段",
                    "自定义说明": "- 只保留 reviewer 需要的补充说明",
                },
                "pr_sections": {
                    "summary": "- 变更目的：精简模板",
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
        self.assertNotIn("## 检查清单", prompt)

    def test_build_prompt_accepts_new_risk_heading(self) -> None:
        meta = {
            "number": 25,
            "title": "治理: 对齐 review template",
            "url": "https://example.test/pr/25",
            "baseRefName": "main",
            "headRefOid": "sha-25",
            "headRefName": "issue-25-branch",
            "body": "## 摘要\n\n- 变更目的：精简模板\n",
        }

        with patch(
            "scripts.pr_guardian.build_review_context",
            return_value={
                "pr_identity": ["- PR: #25"],
                "issue_context": {"identity": [], "summary": ""},
                "item_context": {"issue": "25", "item_key": "GOV-0025-review-template-lean-context"},
                "raw_sections": {
                    "摘要": "- 变更目的：精简模板",
                    "风险": "- 风险级别：`medium`\n- 审查关注：guardian 入口不要回退到模板噪音",
                    "验证": "- python3 -m unittest",
                    "回滚": "- revert PR",
                },
                "pr_sections": {
                    "summary": "- 变更目的：精简模板",
                    "risk": "- 风险级别：`medium`\n- 审查关注：guardian 入口不要回退到模板噪音",
                    "validation": "- python3 -m unittest",
                    "rollback": "- revert PR",
                },
                "changed_files": ["scripts/open_pr.py", ".github/PULL_REQUEST_TEMPLATE.md"],
                "diff_stat": "2 files changed",
                "related_paths": [],
                "context_notes": [],
            },
        ):
            with patch("scripts.pr_guardian.load_reviewer_rubric_excerpt", return_value="## Review Rubric\n- contract 一致性"):
                prompt = build_prompt(meta, Path("/tmp/worktree"))

        self.assertIn("风险摘要：", prompt)
        self.assertIn("审查关注：guardian 入口不要回退到模板噪音", prompt)

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
            "body": "Issue: #24\n## Issue 摘要\n\n- Goal: 精简\n- Scope: 收敛 guardian review context\n",
        }
        worktree_dir = Path("/tmp/pr-worktree")

        with patch("scripts.pr_guardian.fetch_diff_stats", return_value=(["scripts/pr_guardian.py"], "1 file changed")):
            with patch(
                "scripts.pr_guardian.build_item_context_summary",
                return_value=({"issue": "24", "item_key": "GOV-0024-guardian-review-context"}, [], []),
            ) as build_item_context_summary_mock:
                with patch(
                    "scripts.pr_guardian.resolve_issue_canonical_integration",
                    return_value=(24, {}),
                ) as resolve_issue_canonical_integration_mock:
                    with patch(
                        "scripts.pr_guardian.build_review_packet",
                        return_value={},
                    ):
                        with patch(
                            "scripts.pr_guardian.fetch_issue_context",
                            return_value={"identity": [], "summary": "", "canonical_integration": {}},
                        ) as fetch_issue_context_mock:
                            payload = build_review_context(meta, worktree_dir)

        build_item_context_summary_mock.assert_called_once_with(meta, worktree_dir)
        resolve_issue_canonical_integration_mock.assert_called_once_with(meta)
        fetch_issue_context_mock.assert_not_called()
        self.assertEqual(payload["item_context"]["item_key"], "GOV-0024-guardian-review-context")

    def test_build_review_context_keeps_issue_side_evidence_when_item_context_is_invalid(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: 精简 guardian review context",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "Issue: #24\n## 摘要\n\n- item context drift\n",
        }

        with patch("scripts.pr_guardian.fetch_diff_stats", return_value=(["scripts/pr_guardian.py"], "1 file changed")):
            with patch(
                "scripts.pr_guardian.build_item_context_summary",
                return_value=({"item_key": "GOV-0024-guardian-review-context"}, ["item context drift"], []),
            ):
                with patch(
                    "scripts.pr_guardian.resolve_issue_canonical_integration",
                    return_value=(24, {"merge_gate": "integration_check_required"}),
                ) as resolve_issue_canonical_integration_mock:
                    with patch(
                        "scripts.pr_guardian.fetch_issue_context",
                        return_value={"identity": ["- Issue: #24"], "summary": "issue summary", "canonical_integration": {}},
                    ) as fetch_issue_context_mock:
                        with patch(
                            "scripts.pr_guardian.build_review_packet",
                            return_value={"issue_number": 24, "issue_canonical": {"merge_gate": "integration_check_required"}},
                        ) as build_review_packet_mock:
                            payload = build_review_context(meta, Path("/tmp/pr-worktree"))

        resolve_issue_canonical_integration_mock.assert_called_once_with(meta)
        fetch_issue_context_mock.assert_called_once_with(24)
        build_review_packet_mock.assert_called_once()
        self.assertEqual(payload["integration_review_packet"]["issue_number"], 24)
        self.assertEqual(payload["context_notes"], ["item context drift"])

    def test_build_review_context_passes_live_integration_ref_snapshot_to_review_packet(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: integration live snapshot",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "\n".join(
                [
                    "Issue: #24",
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: no",
                ]
            ),
        }

        with patch("scripts.pr_guardian.fetch_diff_stats", return_value=(["scripts/pr_guardian.py"], "1 file changed")):
            with patch(
                "scripts.pr_guardian.build_item_context_summary",
                return_value=({"issue": "24", "item_key": "GOV-0024-guardian-review-context"}, [], []),
            ):
                with patch(
                    "scripts.pr_guardian.resolve_issue_canonical_integration",
                    return_value=(24, {"merge_gate": "integration_check_required"}),
                ):
                    with patch(
                        "scripts.pr_guardian.fetch_issue_context",
                        return_value={"identity": [], "summary": "", "canonical_integration": {}},
                    ):
                        with patch("scripts.pr_guardian.fetch_integration_ref_live_state") as fetch_live_mock:
                            with patch(
                                "scripts.pr_guardian.build_review_packet",
                                return_value={"issue_number": 24},
                            ) as build_review_packet_mock:
                                build_review_context(meta, Path("/tmp/pr-worktree"))

        fetch_live_mock.assert_not_called()
        build_review_packet_mock.assert_called_once()
        kwargs = build_review_packet_mock.call_args.kwargs
        self.assertNotIn("integration_ref_live", kwargs)

    def test_build_review_context_does_not_fetch_live_snapshot_from_issue_canonical_fallback(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: integration live snapshot fallback",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "Issue: #24\n## 摘要\n\n- integration_check 暂未补齐\n",
        }

        with patch("scripts.pr_guardian.fetch_diff_stats", return_value=(["scripts/pr_guardian.py"], "1 file changed")):
            with patch(
                "scripts.pr_guardian.build_item_context_summary",
                return_value=({"issue": "24", "item_key": "GOV-0024-guardian-review-context"}, [], []),
            ):
                with patch(
                    "scripts.pr_guardian.resolve_issue_canonical_integration",
                    return_value=(
                        24,
                        {
                            "integration_touchpoint": "active",
                            "shared_contract_changed": "no",
                            "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                            "external_dependency": "both",
                            "merge_gate": "integration_check_required",
                            "contract_surface": "runtime_modes",
                            "joint_acceptance_needed": "yes",
                        },
                    ),
                ):
                    with patch(
                        "scripts.pr_guardian.fetch_issue_context",
                        return_value={"identity": ["- Issue: #24"], "summary": "issue summary", "canonical_integration": {}},
                    ):
                        with patch("scripts.pr_guardian.fetch_integration_ref_live_state") as fetch_live_mock:
                            with patch(
                                "scripts.pr_guardian.build_review_packet",
                                return_value={"issue_number": 24},
                            ) as build_review_packet_mock:
                                build_review_context(meta, Path("/tmp/pr-worktree"))

        fetch_live_mock.assert_not_called()
        kwargs = build_review_packet_mock.call_args.kwargs
        self.assertNotIn("integration_ref_live", kwargs)

    def test_build_review_context_skips_live_fetch_for_local_only_integration_ref_none(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: local-only integration snapshot",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "\n".join(
                [
                    "Issue: #24",
                    "## integration_check",
                    "",
                    "- integration_touchpoint: none",
                    "- shared_contract_changed: no",
                    "- integration_ref: none",
                    "- external_dependency: none",
                    "- merge_gate: local_only",
                    "- contract_surface: none",
                    "- joint_acceptance_needed: no",
                    "- integration_status_checked_before_pr: no",
                    "- integration_status_checked_before_merge: no",
                ]
            ),
        }

        with patch("scripts.pr_guardian.fetch_diff_stats", return_value=(["scripts/pr_guardian.py"], "1 file changed")):
            with patch(
                "scripts.pr_guardian.build_item_context_summary",
                return_value=({"issue": "24", "item_key": "GOV-0024-guardian-review-context"}, [], []),
            ):
                with patch(
                    "scripts.pr_guardian.resolve_issue_canonical_integration",
                    return_value=(24, {}),
                ):
                    with patch(
                        "scripts.pr_guardian.fetch_issue_context",
                        return_value={"identity": [], "summary": "", "canonical_integration": {}},
                    ):
                        with patch("scripts.pr_guardian.fetch_integration_ref_live_state") as fetch_live_mock:
                            with patch(
                                "scripts.pr_guardian.build_review_packet",
                                return_value={"issue_number": 24},
                            ) as build_review_packet_mock:
                                build_review_context(meta, Path("/tmp/pr-worktree"))

        fetch_live_mock.assert_not_called()
        kwargs = build_review_packet_mock.call_args.kwargs
        self.assertNotIn("integration_ref_live", kwargs)

    def test_build_review_context_keeps_nested_issue_summary_from_pr_body(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: 精简 guardian review context",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "\n".join(
                [
                    "Issue: #24",
                    "## Issue 摘要",
                    "",
                    "## Goal",
                    "",
                    "- 精简 guardian review context",
                    "",
                    "## Scope",
                    "",
                    "- 调整 scripts/pr_guardian.py",
                ]
            ),
        }

        with patch("scripts.pr_guardian.fetch_diff_stats", return_value=(["scripts/pr_guardian.py"], "1 file changed")):
            with patch(
                "scripts.pr_guardian.build_item_context_summary",
                return_value=({"issue": "24", "item_key": "GOV-0024-guardian-review-context"}, [], []),
            ):
                with patch(
                    "scripts.pr_guardian.resolve_issue_canonical_integration",
                    return_value=(24, {}),
                ):
                    with patch(
                        "scripts.pr_guardian.build_review_packet",
                        return_value={},
                    ):
                        with patch(
                            "scripts.pr_guardian.fetch_issue_context",
                            return_value={"identity": [], "summary": "", "canonical_integration": {}},
                        ) as fetch_issue_context_mock:
                            payload = build_review_context(meta, Path("/tmp/pr-worktree"))

        fetch_issue_context_mock.assert_not_called()
        self.assertIn("## Goal", payload["pr_sections"]["issue_summary"])
        self.assertIn("## Scope", payload["pr_sections"]["issue_summary"])

    def test_extract_reviewer_rubric_excerpt_excludes_merge_gate_sections(self) -> None:
        excerpt = extract_reviewer_rubric_excerpt(
            "\n".join(
                [
                    "# 审查标准",
                    "",
                    "## 审查输入",
                    "",
                    "- 不应出现在 reviewer excerpt",
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

        self.assertNotIn("## 审查输入", excerpt)
        self.assertIn("## 工件完整性检查", excerpt)
        self.assertIn("## Review Rubric", excerpt)
        self.assertIn("## 职责边界说明", excerpt)
        self.assertNotIn("## 合并门禁", excerpt)

    def test_render_item_context_supplement_keeps_only_non_redundant_lines(self) -> None:
        supplement = render_item_context_supplement(
            "\n".join(
                [
                    "- Issue: 25",
                    "- item_key: GOV-0025-review-template-lean-context",
                    "- item_type: GOV",
                    "- release: v0.1.0",
                    "- sprint: 2026-S14",
                    "- Closing: Fixes #25",
                    "- 需要 reviewer 关注模板兼容性",
                ]
            )
        )

        self.assertNotIn("item_key", supplement)
        self.assertIn("Fixes #25", supplement)
        self.assertIn("模板兼容性", supplement)

    @patch(
        "scripts.pr_guardian.run",
        return_value=subprocess.CompletedProcess(args=["git"], returncode=1, stdout="", stderr="missing"),
    )
    def test_load_reviewer_rubric_excerpt_falls_back_to_pr_worktree_file(self, run_mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            worktree_dir = Path(temp_dir)
            (worktree_dir / "code_review.md").write_text(
                "\n".join(
                    [
                        "## 工件完整性检查",
                        "",
                        "- 仅使用 worktree 内文件",
                        "",
                        "## Review Rubric",
                        "",
                        "- contract 一致性",
                    ]
                ),
                encoding="utf-8",
            )

            excerpt = load_reviewer_rubric_excerpt(worktree_dir, "main")

        self.assertIn("仅使用 worktree 内文件", excerpt)
        run_mock.assert_called_once()

    @patch(
        "scripts.pr_guardian.run",
        return_value=subprocess.CompletedProcess(
            args=["git"],
            returncode=0,
            stdout="## Review Rubric\n\n- 使用基线 rubric\n",
            stderr="",
        ),
    )
    def test_load_reviewer_rubric_excerpt_prefers_base_snapshot_over_worktree_file(self, run_mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            worktree_dir = Path(temp_dir)
            (worktree_dir / "code_review.md").write_text(
                "## Review Rubric\n\n- 使用 PR worktree 内容\n",
                encoding="utf-8",
            )

            excerpt = load_reviewer_rubric_excerpt(worktree_dir, "main")

        self.assertIn("使用基线 rubric", excerpt)
        self.assertNotIn("使用 PR worktree 内容", excerpt)
        run_mock.assert_called_once()

    def test_build_item_context_summary_keeps_related_paths_on_metadata_mismatch(self) -> None:
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
                        "- release：`v0.1.1`",
                        "- sprint：`2026-S14`",
                        "- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`",
                    ]
                ),
                encoding="utf-8",
            )

            with patch("scripts.pr_guardian.load_item_context_from_exec_plan", return_value={"Issue": "24", "item_key": "GOV-0024-guardian-review-context", "item_type": "GOV", "release": "v0.1.1", "sprint": "2026-S14", "exec_plan": str(exec_plan_path)}):
                with patch(
                    "scripts.pr_guardian.active_exec_plans_for_issue",
                    return_value=[{"item_key": "GOV-0024-guardian-review-context"}],
                ):
                    payload, notes, related_paths = build_item_context_summary(meta, repo_root)

        self.assertEqual(payload["item_key"], "GOV-0024-guardian-review-context")
        self.assertIn("release", notes[0])
        self.assertIn(str(exec_plan_path), related_paths)

    def test_build_item_context_summary_rejects_multiple_active_exec_plans_for_issue(self) -> None:
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
                    ]
                ),
                encoding="utf-8",
            )
            with patch(
                "scripts.pr_guardian.load_item_context_from_exec_plan",
                return_value={
                    "Issue": "24",
                    "item_key": "GOV-0024-guardian-review-context",
                    "item_type": "GOV",
                    "release": "v0.1.0",
                    "sprint": "2026-S14",
                    "exec_plan": str(exec_plan_path),
                },
            ):
                with patch(
                    "scripts.pr_guardian.active_exec_plans_for_issue",
                    return_value=[
                        {"item_key": "GOV-0024-guardian-review-context"},
                        {"item_key": "GOV-0099-other"},
                    ],
                ):
                    payload, notes, related_paths = build_item_context_summary(meta, repo_root)

        self.assertEqual(payload["item_key"], "GOV-0024-guardian-review-context")
        self.assertIn("数量异常", notes[0])
        self.assertIn(str(exec_plan_path), related_paths)

    @patch("scripts.pr_guardian.cleanup")
    @patch("scripts.pr_guardian.run_codex_review")
    @patch("scripts.pr_guardian.save_guardian_result")
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
        save_guardian_result_mock,
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
        save_guardian_result_mock.assert_called_once()
        cleanup_mock.assert_called_once_with(temp_dir)

    def test_build_prompt_preserves_preamble_in_raw_fallback(self) -> None:
        meta = {
            "number": 24,
            "title": "治理: 精简 guardian review context",
            "url": "https://example.test/pr/24",
            "baseRefName": "main",
            "headRefOid": "sha-24",
            "headRefName": "issue-24-branch",
            "body": "额外风险说明：需要注意手工回滚步骤。\\n\\n## 摘要\\n\\n- 变更目的：精简 prompt\\n",
        }

        with patch(
            "scripts.pr_guardian.build_review_context",
            return_value={
                "pr_identity": ["- PR: #24"],
                "issue_context": {"identity": [], "summary": ""},
                "item_context": {"issue": "24"},
                "raw_sections": {
                    "__preamble__": "额外风险说明：需要注意手工回滚步骤。",
                    "摘要": "- 变更目的：精简 prompt",
                },
                "pr_sections": {
                    "summary": "- 变更目的：精简 prompt",
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
        self.assertIn("额外风险说明：需要注意手工回滚步骤。", prompt)


class MergeIfSafeTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._integration_live_state_patcher = patch(
            "scripts.pr_guardian.fetch_integration_ref_live_state",
            return_value={
                "source": "project_item",
                "status": "review",
                "dependency_order": "parallel",
                "joint_acceptance": "ready",
                "owner_repo": "joint",
                "contract_status": "reviewing",
                "blocked": False,
                "error": "",
            },
        )
        self.integration_live_state_mock = self._integration_live_state_patcher.start()

    def tearDown(self) -> None:
        self._integration_live_state_patcher.stop()
        super().tearDown()

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
        find_result_mock.return_value = cached_guardian_result(
            "sha-request-changes",
            "",
            verdict="REQUEST_CHANGES",
            safe_to_merge=False,
            summary="blocked",
        )

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
        find_result_mock.return_value = cached_guardian_result(
            "sha-safe-false",
            "",
            safe_to_merge=False,
            summary="blocked",
        )

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("guardian 认为当前 PR 不安全", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.find_latest_guardian_result", return_value=None)
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_uses_current_pr_body_when_checking_guardian_cache(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        run_mock,
    ) -> None:
        current_meta = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-reviewed",
            "body": "## integration_check\n\n- integration_status_checked_before_pr: yes\n",
        }
        pr_meta_mock.return_value = current_meta
        review_once_mock.return_value = (
            current_meta,
            {
                "verdict": "REQUEST_CHANGES",
                "safe_to_merge": False,
                "summary": "reran",
            },
        )

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("guardian 未给出 APPROVE", str(ctx.exception))
        find_result_mock.assert_called_once_with(1, "sha-reviewed", body=current_meta["body"], require_body_bound=True)
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
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
            "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
        }
        find_result_mock.return_value = cached_guardian_result("sha-1", LOCAL_ONLY_INTEGRATION_CHECK_BODY)
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        exit_code = merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertEqual(exit_code, 0)
        review_once_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        self.assertEqual(all_checks_mock.call_count, 2)
        all_checks_mock.assert_called_with(1)
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
                "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-2",
                "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-2",
                "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
            },
        ]
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-2",
                "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
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
        self.assertEqual(all_checks_mock.call_count, 2)
        all_checks_mock.assert_called_with(1)
        run_mock.assert_called_once_with(
            ["gh", "pr", "merge", "1", "--squash", "--match-head-commit", "sha-2", "--delete-branch"],
            cwd=ANY,
        )

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result", return_value=None)
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_body_drift_after_fresh_review_when_head_is_unchanged(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        reviewed_body = LOCAL_ONLY_INTEGRATION_CHECK_BODY
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-2",
                "body": reviewed_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-2",
                "body": reviewed_body + "\n\n补充说明：review 后被编辑\n",
            },
        ]
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-2",
                "body": reviewed_body,
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh",
            },
        )

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("guardian 审查后 PR 描述已变化", str(ctx.exception))
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        all_checks_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()

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
                "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-3",
                "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-3",
                "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
            },
        ]
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-3",
                "body": LOCAL_ONLY_INTEGRATION_CHECK_BODY,
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
        self.assertEqual(all_checks_mock.call_count, 2)
        all_checks_mock.assert_called_with(1)

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
        find_result_mock.return_value = cached_guardian_result("sha-reviewed", "")

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
        find_result_mock.return_value = cached_guardian_result("sha-green-check", "")

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("GitHub checks 未全部通过", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_contradictory_local_only_integration_metadata(
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
            "headRefOid": "sha-integration-contradiction",
            "body": CONTRADICTORY_LOCAL_ONLY_INTEGRATION_CHECK_BODY,
        }
        find_result_mock.return_value = cached_guardian_result(
            "sha-integration-contradiction",
            CONTRADICTORY_LOCAL_ONLY_INTEGRATION_CHECK_BODY,
        )

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("integration merge gate 未满足", str(ctx.exception))
        self.assertIn("`merge_gate=local_only` 与当前 integration 元数据冲突", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_requires_explicit_merge_time_integration_recheck_confirmation(
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
            "headRefOid": "sha-needs-recheck",
            "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        }
        find_result_mock.return_value = cached_guardian_result(
            "sha-needs-recheck",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(1, post=False, delete_branch=False, refresh_review=False)

        self.assertIn("--confirm-integration-recheck", str(ctx.exception))
        review_once_mock.assert_not_called()
        run_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_records_merge_time_integration_recheck_before_merging(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
        ]
        find_result_mock.return_value = cached_guardian_result(
            "sha-needs-recheck",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh-for-final-body",
            },
        )
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        exit_code = merge_if_safe(
            1,
            post=False,
            delete_branch=False,
            refresh_review=False,
            confirm_integration_recheck=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(run_mock.call_count, 2)
        edit_command = run_mock.call_args_list[0].args[0]
        merge_command = run_mock.call_args_list[1].args[0]
        self.assertEqual(edit_command[:4], ["gh", "pr", "edit", "1"])
        self.assertIn("--body-file", edit_command)
        self.assertEqual(
            merge_command,
            ["gh", "pr", "merge", "1", "--squash", "--match-head-commit", "sha-needs-recheck"],
        )
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        require_auth_mock.assert_called_once()
        self.assertEqual(all_checks_mock.call_count, 2)
        all_checks_mock.assert_called_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_reruns_guardian_when_cached_body_bound_verdict_becomes_stale_after_recheck(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        edited_bodies: list[str] = []

        def run_side_effect(command, cwd=None, check=True):
            if command[:4] == ["gh", "pr", "edit", "1"]:
                body_file = Path(command[command.index("--body-file") + 1])
                edited_bodies.append(body_file.read_text(encoding="utf-8"))
                return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")
            if command[:4] == ["gh", "pr", "merge", "1"]:
                return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")
            raise AssertionError(f"unexpected command: {command}")

        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
        ]
        find_result_mock.return_value = {
            "schema_version": 2,
            "pr_number": 1,
            "head_sha": "sha-needs-recheck",
            "body_fingerprint": guardian_body_fingerprint(INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY),
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "cached",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh-for-final-body",
            },
        )
        run_mock.side_effect = run_side_effect

        exit_code = merge_if_safe(
            1,
            post=False,
            delete_branch=False,
            refresh_review=False,
            confirm_integration_recheck=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(edited_bodies), 1)
        self.assertIn("- integration_status_checked_before_merge: yes", edited_bodies[0])
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(run_mock.call_args_list[1].args[0][:4], ["gh", "pr", "merge", "1"])
        require_auth_mock.assert_called_once()
        self.assertEqual(all_checks_mock.call_count, 2)
        all_checks_mock.assert_called_with(1)

    @patch("scripts.pr_guardian.restore_merge_time_integration_recheck_or_die")
    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_same_head_body_drift_after_recheck_refresh_review(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
        restore_merge_time_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        concurrent_body = updated_body + "\n\n补充说明：refresh 后被编辑\n"

        def run_side_effect(command, cwd=None, check=True):
            if command[:4] == ["gh", "pr", "edit", "1"]:
                return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")
            raise AssertionError(f"unexpected command: {command}")

        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-needs-recheck",
                "body": concurrent_body,
            },
        ]
        find_result_mock.return_value = {
            "schema_version": 2,
            "pr_number": 1,
            "head_sha": "sha-needs-recheck",
            "body_fingerprint": guardian_body_fingerprint(INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY),
            "verdict": "APPROVE",
            "safe_to_merge": True,
            "summary": "cached",
            "reviewed_at": "2026-03-28T10:00:00Z",
        }
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-needs-recheck",
                "body": updated_body,
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh-for-final-body",
            },
        )
        run_mock.side_effect = run_side_effect

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("merge 前重跑 guardian 后 PR 描述已变化", str(ctx.exception))
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        restore_merge_time_mock.assert_called_once()
        self.assertEqual(run_mock.call_count, 1)
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_body_drift_before_recording_merge_time_recheck(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        concurrent_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY + "\n\n补充说明：并发编辑\n"
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": concurrent_body,
            },
        ]
        find_result_mock.return_value = cached_guardian_result(
            "sha-reviewed",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("PR 描述已变化", str(ctx.exception))
        run_mock.assert_not_called()
        review_once_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_restores_recheck_when_refresh_after_record_fails(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        edited_bodies: list[str] = []

        def run_side_effect(command, cwd=None, check=True):
            if command[:4] == ["gh", "pr", "edit", "1"]:
                body_file = Path(command[command.index("--body-file") + 1])
                edited_bodies.append(body_file.read_text(encoding="utf-8"))
                return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")
            raise AssertionError(f"unexpected command: {command}")

        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            SystemExit("refresh failed"),
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
        ]
        find_result_mock.return_value = cached_guardian_result(
            "sha-reviewed",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        run_mock.side_effect = run_side_effect

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("无法重新读取最新 PR 描述", str(ctx.exception))
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(len(edited_bodies), 2)
        self.assertIn("- integration_status_checked_before_merge: yes", edited_bodies[0])
        self.assertIn("- integration_status_checked_before_merge: no", edited_bodies[1])
        review_once_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_does_not_restore_body_when_refresh_after_record_fails(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        edited_bodies: list[str] = []

        def run_side_effect(command, cwd=None, check=True):
            if command[:4] == ["gh", "pr", "edit", "1"]:
                body_file = Path(command[command.index("--body-file") + 1])
                edited_bodies.append(body_file.read_text(encoding="utf-8"))
                return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")
            raise AssertionError(f"unexpected command: {command}")

        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            SystemExit("refresh failed"),
        ]
        find_result_mock.return_value = cached_guardian_result(
            "sha-reviewed",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        run_mock.side_effect = run_side_effect

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("已回滚到旧值", str(ctx.exception))
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(len(edited_bodies), 2)
        self.assertIn("- integration_status_checked_before_merge: no", edited_bodies[1])
        review_once_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_pr_body_drift_after_integration_validation(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        concurrent_body = updated_body + "\n\n补充说明：merge 前又有编辑\n"
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": concurrent_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": concurrent_body,
            },
        ]
        find_result_mock.return_value = cached_guardian_result(
            "sha-reviewed",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh-for-final-body",
            },
        )
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("merge 前重跑 guardian 后 PR 描述已变化", str(ctx.exception))
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(run_mock.call_args_list[0].args[0][:4], ["gh", "pr", "edit", "1"])
        self.assertEqual(run_mock.call_args_list[1].args[0][:4], ["gh", "pr", "edit", "1"])
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_rejects_head_change_after_recording_merge_time_recheck(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-unreviewed",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-unreviewed",
                "body": updated_body.replace(
                    "- integration_status_checked_before_merge: yes",
                    "- integration_status_checked_before_merge: no",
                ),
            },
        ]
        find_result_mock.return_value = cached_guardian_result(
            "sha-reviewed",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="", stderr="")

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("merge 前 integration 复核后 PR HEAD 已变化", str(ctx.exception))
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(run_mock.call_args_list[0].args[0][:4], ["gh", "pr", "edit", "1"])
        self.assertEqual(run_mock.call_args_list[1].args[0][:4], ["gh", "pr", "edit", "1"])
        review_once_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_reverts_merge_time_recheck_when_merge_command_fails(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
        ]
        find_result_mock.return_value = cached_guardian_result(
            "sha-reviewed",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh-for-final-body",
            },
        )
        run_mock.side_effect = [
            subprocess.CompletedProcess(args=["gh", "pr", "edit"], returncode=0, stdout="", stderr=""),
            CommandError(["gh", "pr", "merge", "1"], "命令失败", "", "merge failed"),
            subprocess.CompletedProcess(args=["gh", "pr", "edit"], returncode=0, stdout="", stderr=""),
        ]

        with self.assertRaises(CommandError):
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertEqual(run_mock.call_count, 3)
        self.assertEqual(run_mock.call_args_list[0].args[0][:4], ["gh", "pr", "edit", "1"])
        self.assertEqual(run_mock.call_args_list[1].args[0][:4], ["gh", "pr", "merge", "1"])
        self.assertEqual(run_mock.call_args_list[2].args[0][:4], ["gh", "pr", "edit", "1"])
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        require_auth_mock.assert_called_once()
        self.assertEqual(all_checks_mock.call_count, 2)
        all_checks_mock.assert_called_with(1)

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_does_not_restore_stale_body_over_concurrent_edits(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        updated_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_status_checked_before_merge: no",
            "- integration_status_checked_before_merge: yes",
        )
        concurrent_body = updated_body + "\n\n补充说明：其他人已更新 PR 描述\n"
        pr_meta_mock.side_effect = [
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": concurrent_body,
            },
            {
                "number": 1,
                "isDraft": False,
                "headRefOid": "sha-reviewed",
                "body": concurrent_body,
            },
        ]
        find_result_mock.return_value = cached_guardian_result(
            "sha-reviewed",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        review_once_mock.return_value = (
            {
                "number": 1,
                "headRefOid": "sha-reviewed",
                "body": updated_body,
            },
            {
                "verdict": "APPROVE",
                "safe_to_merge": True,
                "summary": "fresh-for-final-body",
            },
        )
        edited_bodies: list[str] = []

        def run_side_effect(command, cwd=None, check=True):
            if command[:4] == ["gh", "pr", "edit", "1"]:
                body_file = Path(command[command.index("--body-file") + 1])
                edited_bodies.append(body_file.read_text(encoding="utf-8"))
                return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")
            if command[:4] == ["gh", "pr", "merge", "1"]:
                raise CommandError(command, "命令失败", "", "merge failed")
            raise AssertionError(f"unexpected command: {command}")

        run_mock.side_effect = run_side_effect

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("merge 前重跑 guardian 后 PR 描述已变化", str(ctx.exception))
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(run_mock.call_args_list[0].args[0][:4], ["gh", "pr", "edit", "1"])
        self.assertEqual(run_mock.call_args_list[1].args[0][:4], ["gh", "pr", "edit", "1"])
        self.assertEqual(len(edited_bodies), 2)
        self.assertIn("其他人已更新 PR 描述", edited_bodies[1])
        self.assertIn("- integration_status_checked_before_merge: no", edited_bodies[1])
        review_once_mock.assert_called_once_with(1, post=False, json_output=None)
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    def test_fetch_issue_context_parses_issue_form_headings(self) -> None:
        with patch(
            "scripts.pr_guardian.run",
            return_value=subprocess.CompletedProcess(args=["gh"], returncode=0, stdout='{"number": 105, "title": "治理：integration baseline", "url": "https://example.test/issues/105", "body": "### 摘要\\n\\n- 为 Syvert 保留本地执行真相源\\n\\n### 范围\\n\\n- 补齐 integration 联动插槽"}', stderr=""),
        ):
            context = fetch_issue_context(105)

        self.assertIn("- Issue: #105", context["identity"])
        self.assertIn("## Goal", context["summary"])
        self.assertIn("## Scope", context["summary"])

    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_does_not_record_recheck_before_validation_succeeds(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
    ) -> None:
        invalid_body = INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY.replace(
            "- integration_ref: https://github.com/MC-and-his-Agents/WebEnvoy/issues/466",
            "- integration_ref: none",
        )
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-invalid-before-record",
            "body": invalid_body,
        }
        find_result_mock.return_value = cached_guardian_result(
            "sha-invalid-before-record",
            invalid_body,
        )

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("integration merge gate 未满足", str(ctx.exception))
        run_mock.assert_not_called()
        review_once_mock.assert_not_called()
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.fetch_integration_ref_live_state")
    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_blocks_when_live_integration_ref_joint_acceptance_not_ready(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
        fetch_live_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-live-not-ready",
            "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        }
        find_result_mock.return_value = cached_guardian_result(
            "sha-live-not-ready",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        fetch_live_mock.return_value = {
            "source": "project_item",
            "status": "review",
            "dependency_order": "parallel",
            "joint_acceptance": "pending",
            "owner_repo": "joint",
            "contract_status": "reviewing",
            "blocked": False,
            "error": "",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("联合验收状态未就绪", str(ctx.exception))
        run_mock.assert_not_called()
        review_once_mock.assert_not_called()
        fetch_live_mock.assert_called_once_with("https://github.com/MC-and-his-Agents/WebEnvoy/issues/466")
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)

    @patch("scripts.pr_guardian.fetch_integration_ref_live_state")
    @patch("scripts.pr_guardian.run")
    @patch("scripts.pr_guardian.all_checks_pass", return_value=True)
    @patch("scripts.pr_guardian.find_latest_guardian_result")
    @patch("scripts.pr_guardian.pr_meta")
    @patch("scripts.pr_guardian.require_auth")
    @patch("scripts.pr_guardian.review_once")
    def test_merge_blocks_when_live_integration_ref_cannot_be_read(
        self,
        review_once_mock,
        require_auth_mock,
        pr_meta_mock,
        find_result_mock,
        all_checks_mock,
        run_mock,
        fetch_live_mock,
    ) -> None:
        pr_meta_mock.return_value = {
            "number": 1,
            "isDraft": False,
            "headRefOid": "sha-live-unreadable",
            "body": INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        }
        find_result_mock.return_value = cached_guardian_result(
            "sha-live-unreadable",
            INTEGRATION_GATED_PENDING_MERGE_RECHECK_BODY,
        )
        fetch_live_mock.return_value = {
            "source": "project_item",
            "error": "无法读取 `integration_ref` 指向的 project item `PVTI_test`，拒绝继续。",
        }

        with self.assertRaises(SystemExit) as ctx:
            merge_if_safe(
                1,
                post=False,
                delete_branch=False,
                refresh_review=False,
                confirm_integration_recheck=True,
            )

        self.assertIn("无法读取 `integration_ref` 指向的 project item", str(ctx.exception))
        run_mock.assert_not_called()
        review_once_mock.assert_not_called()
        fetch_live_mock.assert_called_once_with("https://github.com/MC-and-his-Agents/WebEnvoy/issues/466")
        require_auth_mock.assert_called_once()
        all_checks_mock.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
