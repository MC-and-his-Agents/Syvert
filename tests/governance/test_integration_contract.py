from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.common import REPO_ROOT, default_github_repo, integration_ref_is_checkable, normalize_integration_ref_for_comparison
from scripts.integration_contract import (
    CONTRACT_SOURCE_MACHINE_READABLE,
    CONTRACT_SOURCE_MODULE,
    FIELD_ORDER,
    ISSUE_SCOPE_FIELDS,
    PR_SCOPE_FIELDS,
    build_review_packet,
    fetch_integration_ref_live_state,
    extract_issue_canonical_integration_fields,
    field_choices,
    markdown_section_label,
    parse_pr_integration_check,
    render_contract_reference_lines,
    render_issue_form_guidance_lines,
    render_pr_template_guidance_lines,
    render_review_packet_lines,
    validate_integration_ref_live_state,
    validate_issue_fetch,
    validate_issue_canonical_payload,
    validate_pr_merge_gate_payload,
)


LOCAL_ONLY_PR_BODY = "\n".join(
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


class IntegrationContractTests(unittest.TestCase):
    def test_scope_fields_follow_contract_order(self) -> None:
        self.assertEqual(ISSUE_SCOPE_FIELDS, FIELD_ORDER[: len(ISSUE_SCOPE_FIELDS)])
        self.assertEqual(PR_SCOPE_FIELDS, FIELD_ORDER)

    def test_normalize_integration_ref_for_comparison_supports_all_documented_forms(self) -> None:
        self.assertEqual(
            normalize_integration_ref_for_comparison("#12"),
            "issue:mc-and-his-agents/syvert#12",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison("MC-and-his-Agents/Syvert#12"),
            "issue:mc-and-his-agents/syvert#12",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison("https://github.com/MC-and-his-Agents/Syvert/issues/12"),
            "issue:mc-and-his-agents/syvert#12",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison(
                "https://github.com/orgs/MC-and-his-Agents/projects/3/views/1?pane=issue&itemId=PVTI_test"
            ),
            "project-item:mc-and-his-agents/3#PVTI_test",
        )
        self.assertEqual(
            normalize_integration_ref_for_comparison(
                "https://github.com/orgs/MC-and-his-Agents/projects/3?itemId=PVTI_test&pane=issue"
            ),
            "project-item:mc-and-his-agents/3#PVTI_test",
        )

    def test_extract_issue_canonical_integration_fields_uses_issue_scope_fields(self) -> None:
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
                "",
                "### integration_status_checked_before_pr",
                "",
                "yes",
            ]
        )

        payload = extract_issue_canonical_integration_fields(body)

        self.assertEqual(tuple(payload.keys()), ISSUE_SCOPE_FIELDS)
        self.assertNotIn("integration_status_checked_before_pr", payload)

    def test_parse_pr_integration_check_uses_full_pr_scope_fields(self) -> None:
        body = "\n".join(
            [
                "## integration_check",
                "",
                "- integration_touchpoint: active",
                "- shared_contract_changed: no",
                "- integration_ref: #12",
                "- external_dependency: both",
                "- merge_gate: integration_check_required",
                "- contract_surface: runtime_modes",
                "- joint_acceptance_needed: yes",
                "- integration_status_checked_before_pr: yes",
                "- integration_status_checked_before_merge: no",
            ]
        )

        payload = parse_pr_integration_check(body)

        self.assertEqual(tuple(payload.keys()), PR_SCOPE_FIELDS)

    def test_build_review_packet_surfaces_issue_and_pr_canonical_metadata(self) -> None:
        packet = build_review_packet(
            "\n".join(
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
                    "- integration_status_checked_before_merge: no",
                ]
            ),
            issue_number=105,
            issue_canonical={
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
            issue_error="",
        )

        self.assertEqual(packet["issue_number"], 105)
        self.assertIn("integration_ref", packet["issue_canonical"])
        self.assertIn("integration_ref", packet["pr_canonical"])
        self.assertEqual(packet["normalized_issue_canonical"]["integration_ref"], "issue:mc-and-his-agents/syvert#12")
        self.assertEqual(packet["normalized_pr_canonical"]["integration_ref"], "issue:mc-and-his-agents/syvert#12")
        self.assertFalse(packet["comparison_errors"])
        self.assertEqual(packet["merge_validation_errors"], [])
        self.assertTrue(packet["merge_gate_requires_recheck"])

    @patch(
        "scripts.integration_contract.fetch_integration_ref_live_state",
        return_value={
            "source": "project_item",
            "content_repo": "MC-and-his-Agents/Syvert",
            "content_issue_number": "12",
            "content_type": "issue",
            "error": "",
        },
    )
    def test_build_review_packet_collapses_equivalent_issue_and_project_item_refs(self, fetch_live_mock) -> None:
        packet = build_review_packet(
            "\n".join(
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
                    "- integration_status_checked_before_merge: no",
                ]
            ),
            issue_number=105,
            issue_canonical={
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "MC-and-his-Agents/Syvert#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
            issue_error="",
        )

        self.assertEqual(packet["comparison_errors"], [])
        self.assertEqual(packet["normalized_issue_canonical"]["integration_ref"], "issue:mc-and-his-agents/syvert#12")
        self.assertEqual(packet["normalized_pr_canonical"]["integration_ref"], "issue:mc-and-his-agents/syvert#12")
        self.assertGreaterEqual(fetch_live_mock.call_count, 1)

    @patch(
        "scripts.integration_contract.fetch_integration_ref_live_state",
        return_value={"source": "project_item", "error": "lookup failed"},
    )
    def test_build_review_packet_fail_closed_when_cross_form_ref_cannot_be_resolved(self, fetch_live_mock) -> None:
        packet = build_review_packet(
            "\n".join(
                [
                    "## integration_check",
                    "",
                    "- integration_touchpoint: active",
                    "- shared_contract_changed: no",
                    "- integration_ref: https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_missing",
                    "- external_dependency: both",
                    "- merge_gate: integration_check_required",
                    "- contract_surface: runtime_modes",
                    "- joint_acceptance_needed: yes",
                    "- integration_status_checked_before_pr: yes",
                    "- integration_status_checked_before_merge: no",
                ]
            ),
            issue_number=105,
            issue_canonical={
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "MC-and-his-Agents/Syvert#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
            issue_error="",
        )

        self.assertEqual(
            packet["comparison_errors"],
            ["`integration_check.integration_ref` 与 Issue #105 中的 canonical integration 元数据不一致。"],
        )
        self.assertGreaterEqual(fetch_live_mock.call_count, 1)

    def test_default_github_repo_uses_repo_root_name_when_env_missing(self) -> None:
        default_github_repo.cache_clear()
        with patch.dict("os.environ", {}, clear=True), patch("scripts.common.REPO_ROOT", Path("/tmp/WebEnvoy")):
            self.assertEqual(default_github_repo(), "MC-and-his-Agents/WebEnvoy")
        default_github_repo.cache_clear()

    def test_default_github_repo_honors_explicit_env_override(self) -> None:
        default_github_repo.cache_clear()
        with patch.dict("os.environ", {"SYVERT_GITHUB_REPO": "MC-and-his-Agents/WebEnvoy"}, clear=True):
            self.assertEqual(default_github_repo(), "MC-and-his-Agents/WebEnvoy")
        default_github_repo.cache_clear()

    def test_default_github_repo_maps_fork_origin_to_canonical_repo(self) -> None:
        default_github_repo.cache_clear()
        with patch.dict("os.environ", {}, clear=True), patch("scripts.common.REPO_ROOT", Path("/tmp/unknown-repo")), patch(
            "scripts.common.run"
        ) as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(
                args=["git"],
                returncode=0,
                stdout="git@github.com:contributor/WebEnvoy.git\n",
                stderr="",
            )

            self.assertEqual(default_github_repo(), "MC-and-his-Agents/WebEnvoy")

        default_github_repo.cache_clear()

    def test_build_review_packet_rejects_missing_pr_canonical_when_issue_declares_contract(self) -> None:
        packet = build_review_packet(
            "## 摘要\n\n- 变更目的：验证 reviewer packet\n",
            issue_number=105,
            issue_canonical={
                "integration_touchpoint": "active",
                "shared_contract_changed": "no",
                "integration_ref": "#12",
                "external_dependency": "both",
                "merge_gate": "integration_check_required",
                "contract_surface": "runtime_modes",
                "joint_acceptance_needed": "yes",
            },
            issue_error="",
        )

        rendered = "\n".join(render_review_packet_lines(packet))
        expected_error = "PR 对应的 Issue #105 已声明 canonical integration 元数据，PR 描述缺少 canonical `integration_check` 段落。"

        self.assertEqual(packet["pr_canonical"], {})
        self.assertEqual(packet["comparison_errors"], [expected_error])
        self.assertEqual(packet["merge_validation_errors"], [expected_error])
        self.assertIn(expected_error, rendered)
        self.assertNotIn("canonical_mismatches: none", rendered)
        self.assertNotIn("merge_gate_validation: ok", rendered)

    def test_build_review_packet_propagates_issue_lookup_error_into_reviewer_packet(self) -> None:
        packet = build_review_packet(
            LOCAL_ONLY_PR_BODY,
            issue_number=105,
            issue_canonical={},
            issue_error="无法读取 Issue #105 的 canonical integration 元数据，拒绝继续。",
        )

        rendered = "\n".join(render_review_packet_lines(packet))
        expected_error = "无法读取 Issue #105 的 canonical integration 元数据，拒绝继续。"

        self.assertEqual(packet["comparison_errors"], [expected_error])
        self.assertEqual(packet["merge_validation_errors"], [expected_error])
        self.assertIn(expected_error, rendered)
        self.assertNotIn("canonical_mismatches: none", rendered)
        self.assertNotIn("merge_gate_validation: ok", rendered)

    def test_build_review_packet_includes_integration_ref_live_snapshot_when_provided(self) -> None:
        packet = build_review_packet(
            "\n".join(
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
                    "- integration_status_checked_before_merge: no",
                ]
            ),
            issue_number=105,
            issue_canonical={},
            issue_error="",
            integration_ref_live={
                "source": "project_item",
                "status": "review",
                "dependency_order": "parallel",
                "joint_acceptance": "ready",
                "owner_repo": "joint",
                "contract_status": "reviewing",
                "url": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
                "error": "",
            },
        )

        rendered = "\n".join(render_review_packet_lines(packet))
        self.assertEqual(packet["integration_ref_live"]["source"], "project_item")
        self.assertEqual(packet["integration_ref_live_errors"], [])
        self.assertIn("integration_ref_live:", rendered)
        self.assertIn("joint_acceptance: ready", rendered)

    def test_validate_integration_ref_live_state_blocks_blocked_status(self) -> None:
        payload = {
            "integration_touchpoint": "active",
            "shared_contract_changed": "no",
            "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
            "external_dependency": "both",
            "merge_gate": "integration_check_required",
            "contract_surface": "runtime_modes",
            "joint_acceptance_needed": "yes",
            "integration_status_checked_before_pr": "yes",
            "integration_status_checked_before_merge": "yes",
        }
        errors = validate_integration_ref_live_state(
            payload,
            {
                "source": "project_item",
                "status": "blocked",
                "dependency_order": "parallel",
                "joint_acceptance": "ready",
                "owner_repo": "joint",
                "contract_status": "reviewing",
                "blocked": True,
                "error": "",
            },
            current_repo_slug="MC-and-his-Agents/Syvert",
        )

        self.assertTrue(any("blocked" in item for item in errors))

    def test_validate_integration_ref_live_state_blocks_unready_joint_acceptance(self) -> None:
        payload = {
            "integration_touchpoint": "active",
            "shared_contract_changed": "no",
            "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
            "external_dependency": "both",
            "merge_gate": "integration_check_required",
            "contract_surface": "runtime_modes",
            "joint_acceptance_needed": "yes",
            "integration_status_checked_before_pr": "yes",
            "integration_status_checked_before_merge": "yes",
        }
        errors = validate_integration_ref_live_state(
            payload,
            {
                "source": "project_item",
                "status": "review",
                "dependency_order": "parallel",
                "joint_acceptance": "pending",
                "owner_repo": "joint",
                "contract_status": "reviewing",
                "blocked": False,
                "error": "",
            },
            current_repo_slug="MC-and-his-Agents/Syvert",
        )

        self.assertTrue(any("联合验收状态未就绪" in item for item in errors))

    def test_validate_integration_ref_live_state_rejects_in_progress_status(self) -> None:
        payload = {
            "integration_touchpoint": "active",
            "shared_contract_changed": "no",
            "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
            "external_dependency": "both",
            "merge_gate": "integration_check_required",
            "contract_surface": "runtime_modes",
            "joint_acceptance_needed": "yes",
            "integration_status_checked_before_pr": "yes",
            "integration_status_checked_before_merge": "yes",
        }
        errors = validate_integration_ref_live_state(
            payload,
            {
                "source": "project_item",
                "status": "in_progress",
                "dependency_order": "parallel",
                "joint_acceptance": "ready",
                "owner_repo": "joint",
                "contract_status": "reviewing",
                "blocked": False,
                "error": "",
            },
            current_repo_slug="MC-and-his-Agents/Syvert",
        )

        self.assertTrue(any("未进入允许合并的状态集合" in item for item in errors))

    def test_validate_integration_ref_live_state_fail_closed_when_status_missing(self) -> None:
        payload = {
            "integration_touchpoint": "active",
            "shared_contract_changed": "no",
            "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
            "external_dependency": "both",
            "merge_gate": "integration_check_required",
            "contract_surface": "runtime_modes",
            "joint_acceptance_needed": "yes",
            "integration_status_checked_before_pr": "yes",
            "integration_status_checked_before_merge": "yes",
        }
        errors = validate_integration_ref_live_state(
            payload,
            {
                "source": "project_item",
                "status": "",
                "dependency_order": "parallel",
                "joint_acceptance": "ready",
                "blocked": False,
                "error": "",
            },
            current_repo_slug="MC-and-his-Agents/Syvert",
        )

        self.assertTrue(any("status" in item for item in errors))

    def test_validate_integration_ref_live_state_fail_closed_when_dependency_missing(self) -> None:
        payload = {
            "integration_touchpoint": "active",
            "shared_contract_changed": "no",
            "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
            "external_dependency": "both",
            "merge_gate": "integration_check_required",
            "contract_surface": "runtime_modes",
            "joint_acceptance_needed": "yes",
            "integration_status_checked_before_pr": "yes",
            "integration_status_checked_before_merge": "yes",
        }
        errors = validate_integration_ref_live_state(
            payload,
            {
                "source": "project_item",
                "status": "review",
                "dependency_order": "",
                "joint_acceptance": "ready",
                "blocked": False,
                "error": "",
            },
            current_repo_slug="MC-and-his-Agents/Syvert",
        )

        self.assertTrue(any("dependency_order" in item for item in errors))

    def test_validate_integration_ref_live_state_blocks_webenvoy_first_for_syvert(self) -> None:
        payload = {
            "integration_touchpoint": "active",
            "shared_contract_changed": "no",
            "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
            "external_dependency": "both",
            "merge_gate": "integration_check_required",
            "contract_surface": "runtime_modes",
            "joint_acceptance_needed": "yes",
            "integration_status_checked_before_pr": "yes",
            "integration_status_checked_before_merge": "yes",
        }
        errors = validate_integration_ref_live_state(
            payload,
            {
                "source": "project_item",
                "status": "review",
                "dependency_order": "webenvoy_first",
                "joint_acceptance": "ready",
                "owner_repo": "joint",
                "contract_status": "reviewing",
                "blocked": False,
                "error": "",
            },
            current_repo_slug="MC-and-his-Agents/Syvert",
        )

        self.assertTrue(any("webenvoy_first" in item for item in errors))

    def test_validate_integration_ref_live_state_blocks_syvert_first_for_webenvoy(self) -> None:
        payload = {
            "integration_touchpoint": "active",
            "shared_contract_changed": "no",
            "integration_ref": "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test",
            "external_dependency": "both",
            "merge_gate": "integration_check_required",
            "contract_surface": "runtime_modes",
            "joint_acceptance_needed": "yes",
            "integration_status_checked_before_pr": "yes",
            "integration_status_checked_before_merge": "yes",
        }
        errors = validate_integration_ref_live_state(
            payload,
            {
                "source": "project_item",
                "status": "review",
                "dependency_order": "syvert_first",
                "joint_acceptance": "ready",
                "owner_repo": "joint",
                "contract_status": "reviewing",
                "blocked": False,
                "error": "",
            },
            current_repo_slug="MC-and-his-Agents/WebEnvoy",
        )

        self.assertTrue(any("syvert_first" in item for item in errors))

    def test_fetch_integration_ref_live_state_returns_error_for_unreadable_issue(self) -> None:
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value.returncode = 1
            run_mock.return_value.stdout = ""
            run_mock.return_value.stderr = "not found"

            payload = fetch_integration_ref_live_state("MC-and-his-Agents/Syvert#105")

        self.assertEqual(payload["source"], "issue")
        self.assertIn("无法读取", payload["error"])

    def test_fetch_integration_ref_live_state_fail_closed_on_malformed_issue_json(self) -> None:
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="not-json", stderr="")

            payload = fetch_integration_ref_live_state("MC-and-his-Agents/Syvert#105")

        self.assertEqual(payload["source"], "issue")
        self.assertIn("无法解析", payload["error"])

    def test_fetch_integration_ref_live_state_fail_closed_on_malformed_project_item_json(self) -> None:
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="not-json", stderr="")

            payload = fetch_integration_ref_live_state(
                "https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test"
            )

        self.assertEqual(payload["source"], "project_item")
        self.assertIn("无法解析", payload["error"])

    def test_validate_issue_fetch_fail_closed_on_malformed_issue_json(self) -> None:
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="not-json", stderr="")

            resolution = validate_issue_fetch(105, allow_missing_payload=False)

        self.assertIn("无法解析", resolution.error or "")

    def test_integration_ref_is_checkable_matches_project_item_parser_shape(self) -> None:
        self.assertFalse(
            integration_ref_is_checkable("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&foo=itemId=PVTI_test")
        )
        self.assertTrue(
            integration_ref_is_checkable("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test")
        )

    def test_fetch_integration_ref_live_state_reads_issue_ref_from_integration_project_item(self) -> None:
        graphql_payload = {
            "data": {
                "repository": {
                    "issue": {
                        "number": 105,
                        "title": "integration baseline",
                        "url": "https://github.com/MC-and-his-Agents/Syvert/issues/105",
                        "state": "OPEN",
                        "projectItems": {
                            "nodes": [
                                {
                                    "__typename": "ProjectV2Item",
                                    "id": "PVTI_ready",
                                    "isArchived": False,
                                    "fieldValues": {
                                        "nodes": [
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "In Progress",
                                                "field": {"name": "Status"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "parallel",
                                                "field": {"name": "Dependency Order"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "ready",
                                                "field": {"name": "Joint Acceptance"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "reviewing",
                                                "field": {"name": "Contract Status"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "joint",
                                                "field": {"name": "Owner Repo"},
                                            },
                                        ]
                                    },
                                    "project": {
                                        "url": "https://github.com/orgs/MC-and-his-Agents/projects/3",
                                        "number": 3,
                                        "title": "Syvert × WebEnvoy Integration",
                                        "owner": {"login": "MC-and-his-Agents"},
                                    },
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value.returncode = 0
            run_mock.return_value.stdout = json.dumps(graphql_payload)
            run_mock.return_value.stderr = ""

            payload = fetch_integration_ref_live_state("MC-and-his-Agents/Syvert#105")

        self.assertEqual(payload["source"], "issue")
        self.assertEqual(payload["status"], "in_progress")
        self.assertEqual(payload["dependency_order"], "parallel")
        self.assertEqual(payload["joint_acceptance"], "ready")
        self.assertEqual(payload["project_url"], "https://github.com/orgs/MC-and-his-Agents/projects/3")
        self.assertEqual(payload["title"], "integration baseline")
        self.assertEqual(payload["content_type"], "issue")
        self.assertEqual(payload["content_repo"], "MC-and-his-Agents/Syvert")
        self.assertEqual(payload["content_issue_number"], "105")

    def test_fetch_integration_ref_live_state_rejects_issue_without_integration_project_item(self) -> None:
        graphql_payload = {
            "data": {
                "repository": {
                    "issue": {
                        "number": 105,
                        "title": "integration baseline",
                        "url": "https://github.com/MC-and-his-Agents/Syvert/issues/105",
                        "state": "OPEN",
                        "projectItems": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}},
                    }
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value.returncode = 0
            run_mock.return_value.stdout = json.dumps(graphql_payload)
            run_mock.return_value.stderr = ""

            payload = fetch_integration_ref_live_state("MC-and-his-Agents/Syvert#105")

        self.assertEqual(payload["source"], "issue")
        self.assertIn("未挂接可核查的 integration project item", payload["error"])

    def test_fetch_integration_ref_live_state_ignores_non_canonical_project_items(self) -> None:
        graphql_payload = {
            "data": {
                "repository": {
                    "issue": {
                        "number": 105,
                        "title": "integration baseline",
                        "url": "https://github.com/MC-and-his-Agents/Syvert/issues/105",
                        "state": "OPEN",
                        "projectItems": {
                            "nodes": [
                                {
                                    "__typename": "ProjectV2Item",
                                    "id": "PVTI_wrong",
                                    "isArchived": False,
                                    "fieldValues": {
                                        "nodes": [
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "In Progress",
                                                "field": {"name": "Status"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "parallel",
                                                "field": {"name": "Dependency Order"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "ready",
                                                "field": {"name": "Joint Acceptance"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "reviewing",
                                                "field": {"name": "Contract Status"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "joint",
                                                "field": {"name": "Owner Repo"},
                                            },
                                        ]
                                    },
                                    "project": {
                                        "url": "https://github.com/orgs/MC-and-his-Agents/projects/99",
                                        "number": 99,
                                        "title": "Some Other Project",
                                        "owner": {"login": "MC-and-his-Agents"},
                                    },
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value.returncode = 0
            run_mock.return_value.stdout = json.dumps(graphql_payload)
            run_mock.return_value.stderr = ""

            payload = fetch_integration_ref_live_state("MC-and-his-Agents/Syvert#105")

        self.assertEqual(payload["source"], "issue")
        self.assertIn("未挂接可核查的 integration project item", payload["error"])

    def test_fetch_integration_ref_live_state_paginates_issue_project_items(self) -> None:
        first_page = {
            "data": {
                "repository": {
                    "issue": {
                        "number": 105,
                        "title": "integration baseline",
                        "url": "https://github.com/MC-and-his-Agents/Syvert/issues/105",
                        "state": "OPEN",
                        "projectItems": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": True, "endCursor": "cursor-2"},
                        },
                    }
                }
            }
        }
        second_page = {
            "data": {
                "repository": {
                    "issue": {
                        "number": 105,
                        "title": "integration baseline",
                        "url": "https://github.com/MC-and-his-Agents/Syvert/issues/105",
                        "state": "OPEN",
                        "projectItems": {
                            "nodes": [
                                {
                                    "__typename": "ProjectV2Item",
                                    "id": "PVTI_ready",
                                    "isArchived": False,
                                    "fieldValues": {
                                        "nodes": [
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "In Progress",
                                                "field": {"name": "Status"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "parallel",
                                                "field": {"name": "Dependency Order"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "ready",
                                                "field": {"name": "Joint Acceptance"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "reviewing",
                                                "field": {"name": "Contract Status"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "joint",
                                                "field": {"name": "Owner Repo"},
                                            },
                                        ]
                                    },
                                    "project": {
                                        "url": "https://github.com/orgs/MC-and-his-Agents/projects/3",
                                        "number": 3,
                                        "title": "Syvert × WebEnvoy Integration",
                                        "owner": {"login": "MC-and-his-Agents"},
                                    },
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.side_effect = [
                subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=json.dumps(first_page), stderr=""),
                subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=json.dumps(second_page), stderr=""),
            ]

            payload = fetch_integration_ref_live_state("MC-and-his-Agents/Syvert#105")

        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(payload["source"], "issue")
        self.assertEqual(payload["joint_acceptance"], "ready")

    def test_fetch_integration_ref_live_state_rejects_issue_path_project_with_wrong_number(self) -> None:
        graphql_payload = {
            "data": {
                "repository": {
                    "issue": {
                        "number": 105,
                        "title": "integration baseline",
                        "url": "https://github.com/MC-and-his-Agents/Syvert/issues/105",
                        "state": "OPEN",
                        "projectItems": {
                            "nodes": [
                                {
                                    "__typename": "ProjectV2Item",
                                    "id": "PVTI_wrong_number",
                                    "isArchived": False,
                                    "fieldValues": {
                                        "nodes": [
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "Review",
                                                "field": {"name": "Status"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "parallel",
                                                "field": {"name": "Dependency Order"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "ready",
                                                "field": {"name": "Joint Acceptance"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "reviewing",
                                                "field": {"name": "Contract Status"},
                                            },
                                            {
                                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                                "name": "joint",
                                                "field": {"name": "Owner Repo"},
                                            },
                                        ]
                                    },
                                    "project": {
                                        "url": "https://github.com/orgs/MC-and-his-Agents/projects/99",
                                        "number": 99,
                                        "title": "Syvert × WebEnvoy Integration",
                                        "owner": {"login": "MC-and-his-Agents"},
                                    },
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout=json.dumps(graphql_payload), stderr="")

            payload = fetch_integration_ref_live_state("MC-and-his-Agents/Syvert#105")

        self.assertEqual(payload["source"], "issue")
        self.assertIn("未挂接可核查的 integration project item", payload["error"])

    def test_fetch_integration_ref_live_state_rejects_project_item_owner_mismatch(self) -> None:
        graphql_payload = {
            "data": {
                "node": {
                    "__typename": "ProjectV2Item",
                    "isArchived": False,
                    "fieldValues": {
                        "nodes": [
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "In Progress",
                                "field": {"name": "Status"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "parallel",
                                "field": {"name": "Dependency Order"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "ready",
                                "field": {"name": "Joint Acceptance"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "reviewing",
                                "field": {"name": "Contract Status"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "joint",
                                "field": {"name": "Owner Repo"},
                            },
                        ]
                    },
                    "project": {
                        "url": "https://github.com/orgs/another-owner/projects/3",
                        "number": 3,
                        "title": "Syvert × WebEnvoy Integration",
                        "owner": {"login": "another-owner"},
                    },
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value.returncode = 0
            run_mock.return_value.stdout = json.dumps(graphql_payload)
            run_mock.return_value.stderr = ""

            payload = fetch_integration_ref_live_state("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test")

        self.assertEqual(payload["source"], "project_item")
        self.assertIn("canonical integration project item", payload["error"])

    def test_fetch_integration_ref_live_state_rejects_project_item_without_issue_content(self) -> None:
        graphql_payload = {
            "data": {
                "node": {
                    "__typename": "ProjectV2Item",
                    "isArchived": False,
                    "fieldValues": {
                        "nodes": [
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "Review",
                                "field": {"name": "Status"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "parallel",
                                "field": {"name": "Dependency Order"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "ready",
                                "field": {"name": "Joint Acceptance"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "reviewing",
                                "field": {"name": "Contract Status"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "joint",
                                "field": {"name": "Owner Repo"},
                            },
                        ]
                    },
                    "project": {
                        "url": "https://github.com/orgs/MC-and-his-Agents/projects/3",
                        "number": 3,
                        "title": "Syvert × WebEnvoy Integration",
                        "owner": {"login": "MC-and-his-Agents"},
                    },
                    "content": {
                        "__typename": "DraftIssue",
                    },
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value.returncode = 0
            run_mock.return_value.stdout = json.dumps(graphql_payload)
            run_mock.return_value.stderr = ""

            payload = fetch_integration_ref_live_state("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test")

        self.assertEqual(payload["source"], "project_item")
        self.assertIn("必须绑定到可核查的 Issue 内容", payload["error"])

    def test_fetch_integration_ref_live_state_rejects_non_canonical_project_item(self) -> None:
        graphql_payload = {
            "data": {
                "node": {
                    "__typename": "ProjectV2Item",
                    "isArchived": False,
                    "fieldValues": {
                        "nodes": [
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "In Progress",
                                "field": {"name": "Status"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "parallel",
                                "field": {"name": "Dependency Order"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "ready",
                                "field": {"name": "Joint Acceptance"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "reviewing",
                                "field": {"name": "Contract Status"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "joint",
                                "field": {"name": "Owner Repo"},
                            },
                        ]
                    },
                    "project": {
                        "url": "https://github.com/orgs/MC-and-his-Agents/projects/3",
                        "number": 3,
                        "title": "Some Other Project",
                        "owner": {"login": "MC-and-his-Agents"},
                    },
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value.returncode = 0
            run_mock.return_value.stdout = json.dumps(graphql_payload)
            run_mock.return_value.stderr = ""

            payload = fetch_integration_ref_live_state("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test")

        self.assertEqual(payload["source"], "project_item")
        self.assertIn("canonical integration project item", payload["error"])

    def test_fetch_integration_ref_live_state_rejects_project_item_missing_required_canonical_fields(self) -> None:
        graphql_payload = {
            "data": {
                "node": {
                    "__typename": "ProjectV2Item",
                    "isArchived": False,
                    "fieldValues": {
                        "nodes": [
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "In Progress",
                                "field": {"name": "Status"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "parallel",
                                "field": {"name": "Dependency Order"},
                            },
                            {
                                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                                "name": "ready",
                                "field": {"name": "Joint Acceptance"},
                            },
                        ]
                    },
                    "project": {
                        "url": "https://github.com/orgs/MC-and-his-Agents/projects/3",
                        "number": 3,
                        "title": "Syvert × WebEnvoy Integration",
                        "owner": {"login": "MC-and-his-Agents"},
                    },
                }
            }
        }
        with patch("scripts.integration_contract.run") as run_mock:
            run_mock.return_value.returncode = 0
            run_mock.return_value.stdout = json.dumps(graphql_payload)
            run_mock.return_value.stderr = ""

            payload = fetch_integration_ref_live_state("https://github.com/orgs/MC-and-his-Agents/projects/3?pane=issue&itemId=PVTI_test")

        self.assertEqual(payload["source"], "project_item")
        self.assertIn("canonical integration project item", payload["error"])

    def test_validate_pr_merge_gate_payload_keeps_legacy_compatibility_decision_outside_payload_validation(self) -> None:
        payload = {
            "integration_touchpoint": "none",
            "shared_contract_changed": "no",
            "integration_ref": "none",
            "external_dependency": "none",
            "merge_gate": "local_only",
            "contract_surface": "none",
            "joint_acceptance_needed": "no",
            "integration_status_checked_before_pr": "no",
            "integration_status_checked_before_merge": "no",
        }

        errors = validate_pr_merge_gate_payload(
            payload,
            issue_number=None,
            issue_canonical={},
            require_merge_time_recheck=True,
        )

        self.assertEqual(errors, [])

    def test_validate_issue_canonical_payload_enforces_contract_combinations(self) -> None:
        payload = {
            "integration_touchpoint": "active",
            "shared_contract_changed": "no",
            "integration_ref": "none",
            "external_dependency": "both",
            "merge_gate": "local_only",
            "contract_surface": "runtime_modes",
            "joint_acceptance_needed": "yes",
        }

        errors = validate_issue_canonical_payload(payload)

        self.assertTrue(errors)
        self.assertTrue(
            any("Issue canonical integration 元数据与 contract 组合约束冲突" in item for item in errors)
        )

if __name__ == "__main__":
    unittest.main()
