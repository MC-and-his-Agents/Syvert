from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch

from scripts import governance_gate


GOVERNANCE_SCOPE_REPORT = {
    "pr_class": "governance",
    "changed_paths": ["scripts/context_guard.py"],
    "categories": ["governance"],
    "allowed_categories": ["docs", "governance", "spec"],
    "violations": [],
}

IMPLEMENTATION_SCOPE_REPORT = {
    "pr_class": "implementation",
    "changed_paths": ["src/app.py"],
    "categories": ["implementation"],
    "allowed_categories": ["docs", "implementation"],
    "violations": [],
}

SPEC_SCOPE_REPORT = {
    "pr_class": "spec",
    "changed_paths": ["docs/specs/FR-0001-example/spec.md"],
    "categories": ["spec"],
    "allowed_categories": ["docs", "spec"],
    "violations": [],
}


def write_minimal_loom_carrier(root: Path) -> None:
    summary = "carrier validation passed"
    surfaces = ("admission", "review", "merge_ready", "closeout")
    for relative in governance_gate.REQUIRED_LOOM_CARRIER_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".py":
            path.write_text("print('ok')\n", encoding="utf-8")
        elif path.suffix == ".json":
            path.write_text(json.dumps({}), encoding="utf-8")
        else:
            path.write_text("ok\n", encoding="utf-8")
    (root / ".loom/work-items").mkdir(parents=True, exist_ok=True)
    (root / ".loom/progress").mkdir(parents=True, exist_ok=True)
    (root / ".loom/status").mkdir(parents=True, exist_ok=True)
    (root / ".loom/reviews").mkdir(parents=True, exist_ok=True)
    (root / ".loom/shadow").mkdir(parents=True, exist_ok=True)
    (root / ".loom/specs/INIT-0001").mkdir(parents=True, exist_ok=True)
    (root / "WORKFLOW.md").write_text("# Workflow\n\nSyvert repo-native governance surface.\n", encoding="utf-8")
    (root / "code_review.md").write_text("# Code Review\n", encoding="utf-8")
    (root / "docs/process").mkdir(parents=True, exist_ok=True)
    (root / "docs/process/delivery-funnel.md").write_text("# Delivery Funnel\n", encoding="utf-8")
    (root / "scripts/policy").mkdir(parents=True, exist_ok=True)
    (root / "scripts/workflow_guard.py").write_text("print('workflow')\n", encoding="utf-8")
    (root / "scripts/governance_gate.py").write_text("print('governance')\n", encoding="utf-8")
    (root / "scripts/pr_guardian.py").write_text("print('guardian')\n", encoding="utf-8")
    (root / "scripts/policy/integration_contract.json").write_text("{}", encoding="utf-8")
    (root / ".loom/work-items/INIT-0001.md").write_text(
        "\n".join(
            [
                "- Item ID: INIT-0001",
                "- Goal: Adopt Loom",
                "- Scope: Validate carrier",
                "- Execution Path: governance/loom",
                "- Workspace Entry: .",
                "- Recovery Entry: .loom/progress/INIT-0001.md",
                "- Review Entry: .loom/reviews/INIT-0001.json",
                "- Validation Entry: python3 .loom/bin/loom_init.py verify --target .",
                "- Closing Condition: carrier is valid",
                "",
            ]
        ),
        encoding="utf-8",
    )
    status_text = "\n".join(
        [
            "- Item ID: INIT-0001",
            "- Goal: Adopt Loom",
            "- Scope: Validate carrier",
            "- Execution Path: governance/loom",
            "- Workspace Entry: .",
            "- Recovery Entry: .loom/progress/INIT-0001.md",
            "- Review Entry: .loom/reviews/INIT-0001.json",
            "- Validation Entry: python3 .loom/bin/loom_init.py verify --target .",
            "- Closing Condition: carrier is valid",
            "- Current Checkpoint: merge checkpoint",
            f"- Latest Validation Summary: {summary}",
            "",
        ]
    )
    (root / ".loom/status/current.md").write_text(status_text, encoding="utf-8")
    (root / ".loom/progress/INIT-0001.md").write_text(
        "\n".join(
            [
                "- Item ID: INIT-0001",
                "- Current Checkpoint: merge checkpoint",
                f"- Latest Validation Summary: {summary}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for relative, kind in (
        (".loom/reviews/INIT-0001.json", "general_review"),
        (".loom/reviews/INIT-0001.spec.json", "spec_review"),
    ):
        (root / relative).write_text(
            json.dumps(
                {
                    "schema_version": "loom-review/v1",
                    "item_id": "INIT-0001",
                    "decision": "allow",
                    "kind": kind,
                    "summary": "ok",
                    "reviewer": "test",
                    "reviewed_head": "abc",
                    "reviewed_validation_summary": summary,
                }
            ),
            encoding="utf-8",
        )
    for name in ("spec.md", "plan.md", "implementation-contract.md"):
        (root / ".loom/specs/INIT-0001" / name).write_text("ok\n", encoding="utf-8")
    (root / ".loom/companion/README.md").write_text("# Companion\n", encoding="utf-8")
    (root / ".loom/companion/manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "loom-repo-companion-manifest/v1",
                "companion_entry": ".loom/companion/README.md",
                "repo_interface": ".loom/companion/repo-interface.json",
            }
        ),
        encoding="utf-8",
    )
    (root / ".loom/companion/repo-interface.json").write_text(
        json.dumps(
            {
                "schema_version": "loom-repo-interface/v2",
                "companion_entry": ".loom/companion/README.md",
                "repo_specific_requirements": {
                    "admission": [],
                    "review": [
                        {
                            "id": "syvert-review-rubric",
                            "summary": "review",
                            "locator": "code_review.md",
                            "enforcement": "blocking",
                        }
                    ],
                    "merge_ready": [
                        {
                            "id": "syvert-guardian-merge-gate",
                            "summary": "merge",
                            "locator": "code_review.md",
                            "enforcement": "blocking",
                        }
                    ],
                    "closeout": [
                        {
                            "id": "syvert-delivery-closeout",
                            "summary": "closeout",
                            "locator": "docs/process/delivery-funnel.md",
                            "enforcement": "advisory",
                        }
                    ],
                },
                "specialized_gates": [
                    {
                        "id": "workflow-guard",
                        "summary": "workflow",
                        "locator": "scripts/workflow_guard.py",
                        "gate_type": "admission",
                    },
                    {
                        "id": "governance-gate",
                        "summary": "governance",
                        "locator": "scripts/governance_gate.py",
                        "gate_type": "build",
                    },
                    {
                        "id": "pr-guardian",
                        "summary": "guardian",
                        "locator": "scripts/pr_guardian.py",
                        "gate_type": "merge_ready",
                    },
                ],
                "metadata_contract": {
                    "fields": [
                        {
                            "id": "integration_check",
                            "summary": "integration",
                            "applicability_locator": "WORKFLOW.md",
                            "authority_locator": "scripts/policy/integration_contract.json",
                            "enforcement": "blocking",
                        }
                    ]
                },
                "context_schema": {
                    "fields": [
                        {
                            "id": "issue",
                            "summary": "issue",
                            "authority_locator": "WORKFLOW.md",
                            "mapping_rule_locator": "docs/process/delivery-funnel.md",
                            "type": "integer",
                            "required": True,
                        }
                    ]
                    + [
                        {
                            "id": field,
                            "summary": field,
                            "authority_locator": "WORKFLOW.md",
                            "mapping_rule_locator": "WORKFLOW.md",
                            "type": "string",
                            "required": True,
                        }
                        for field in ("item_key", "item_type", "release", "sprint")
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    interop_payload = {
        "schema_version": "loom-repo-interop/v1",
        "host_adapters": [],
        "repo_native_carriers": [],
        "shadow_surfaces": {
            surface: {
                "summary": f"{surface} parity",
                "loom_locator": f".loom/shadow/{surface.replace('_', '-')}-loom.json",
                "repo_locator": f".loom/shadow/{surface.replace('_', '-')}-repo.json",
            }
            for surface in surfaces
        },
    }
    (root / ".loom/companion/interop.json").write_text(json.dumps(interop_payload), encoding="utf-8")
    loom_sources: list[str] = []
    repo_sources: list[str] = []
    for surface in surfaces:
        parity_value = f"{surface}-parity"
        for side, sources in (
            ("loom", [".loom/work-items/INIT-0001.md"]),
            ("repo", ["WORKFLOW.md"]),
        ):
            locator = f".loom/shadow/{surface.replace('_', '-')}-{side}.json"
            source_hashes = {
                source: governance_gate.sha256_file(root / source)
                for source in sources
            }
            (root / locator).write_text(
                json.dumps(
                    {
                        "schema_version": "loom-shadow-surface-evidence/v1",
                        "surface": surface,
                        "side": side,
                        "parity_value": parity_value,
                        "source_files": sources,
                        "source_sha256": source_hashes,
                    }
                ),
                encoding="utf-8",
            )
            if side == "loom":
                loom_sources.append(locator)
            else:
                repo_sources.append(locator)
    (root / ".loom/shadow/shadow-parity.json").write_text(
        json.dumps(
            {
                "schema_version": "loom-shadow-parity-evidence/v1",
                "result": "pass",
                "surfaces": list(surfaces),
                "loom_sources": loom_sources,
                "repo_sources": repo_sources,
            }
        ),
        encoding="utf-8",
    )
    carrier_paths = sorted(
        {
            str(path)
            for path in governance_gate.REQUIRED_LOOM_CARRIER_FILES
        }
        | {
            ".loom/work-items/INIT-0001.md",
            ".loom/progress/INIT-0001.md",
            ".loom/reviews/INIT-0001.json",
            ".loom/reviews/INIT-0001.spec.json",
            ".loom/specs/INIT-0001/spec.md",
            ".loom/specs/INIT-0001/plan.md",
            ".loom/specs/INIT-0001/implementation-contract.md",
        }
        | set(loom_sources)
        | set(repo_sources)
    )
    work_item_path = root / ".loom/work-items/INIT-0001.md"
    work_item_path.write_text(
        work_item_path.read_text(encoding="utf-8")
        + "\n## Associated Artifacts\n\n"
        + "\n".join(f"- `{path}`" for path in carrier_paths)
        + "\n",
        encoding="utf-8",
    )
    (root / ".loom/bootstrap/manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "loom-bootstrap-manifest/v1",
                "artifacts": [
                    {"path": path, "kind": "carrier", "source": "test"}
                    for path in carrier_paths
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / ".loom/bootstrap/init-result.json").write_text(
        json.dumps(
            {
                "schema_version": "loom-init-output/v1",
                "fact_chain": {
                    "mode": "work-item + recovery-entry + derived status-surface",
                    "read_entry": "python3 .loom/bin/loom_init.py fact-chain --target .",
                    "entry_points": {
                        "current_item_id": "INIT-0001",
                        "work_item": ".loom/work-items/INIT-0001.md",
                        "recovery_entry": ".loom/progress/INIT-0001.md",
                        "status_surface": ".loom/status/current.md",
                    },
                },
                "initial_artifacts": [
                    {"path": path, "kind": "carrier", "source": "test"}
                    for path in carrier_paths
                ],
                "initial_work_items": [
                    {
                        "id": "INIT-0001",
                        "goal": "Adopt Loom",
                        "scope": "Validate carrier",
                        "execution_path": "governance/loom",
                        "workspace_entry": ".",
                        "recovery_entry": ".loom/progress/INIT-0001.md",
                        "review_entry": ".loom/reviews/INIT-0001.json",
                        "validation_entry": "python3 .loom/bin/loom_init.py verify --target .",
                        "closing_condition": "carrier is valid",
                        "artifacts": carrier_paths,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    for evidence_path in root.glob(".loom/shadow/*-*.json"):
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        payload["source_sha256"] = {
            source: governance_gate.sha256_file(root / source)
            for source in payload.get("source_files", [])
        }
        evidence_path.write_text(json.dumps(payload), encoding="utf-8")


class GovernanceGateTests(unittest.TestCase):
    @patch("scripts.governance_gate.matching_exec_plan_for_issue", return_value={})
    @patch("scripts.governance_gate.build_report", return_value=GOVERNANCE_SCOPE_REPORT)
    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["scripts/context_guard.py"])
    @patch("scripts.governance_gate.git_current_branch", return_value="HEAD")
    def test_prefers_head_ref_for_current_issue_in_ci(
        self,
        current_branch_mock,
        changed_files_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
        build_report_mock,
        matching_exec_plan_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "refs/heads/issue-57-demo"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(context_rules_mock.call_args.kwargs["current_issue"], 57)
        current_branch_mock.assert_not_called()
        changed_files_mock.assert_called_once()
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()
        build_report_mock.assert_called_once_with("governance", ["scripts/context_guard.py"])
        matching_exec_plan_mock.assert_called_once()

    @patch("scripts.governance_gate.matching_exec_plan_for_issue", return_value={})
    @patch("scripts.governance_gate.build_report", return_value=GOVERNANCE_SCOPE_REPORT)
    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["scripts/context_guard.py"])
    @patch("scripts.governance_gate.git_current_branch", return_value="issue-57-demo")
    def test_falls_back_to_current_branch_when_head_ref_has_no_issue(
        self,
        current_branch_mock,
        changed_files_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
        build_report_mock,
        matching_exec_plan_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "HEAD"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(context_rules_mock.call_args.kwargs["current_issue"], 57)
        current_branch_mock.assert_called_once()
        changed_files_mock.assert_called_once()
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()
        build_report_mock.assert_called_once_with("governance", ["scripts/context_guard.py"])
        matching_exec_plan_mock.assert_called_once()

    @patch("scripts.governance_gate.matching_exec_plan_for_issue", return_value={})
    @patch("scripts.governance_gate.build_report", return_value=IMPLEMENTATION_SCOPE_REPORT)
    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["src/app.py"])
    @patch("scripts.governance_gate.git_current_branch", return_value="issue-57-demo")
    def test_implementation_diff_uses_implementation_scope_contract(
        self,
        current_branch_mock,
        changed_files_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
        build_report_mock,
        matching_exec_plan_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "HEAD"])

        self.assertEqual(exit_code, 0)
        current_branch_mock.assert_called_once()
        changed_files_mock.assert_called_once()
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()
        context_rules_mock.assert_called_once()
        build_report_mock.assert_called_once_with("implementation", ["src/app.py"])
        matching_exec_plan_mock.assert_called_once()

    @patch("scripts.governance_gate.validate_pr_preflight")
    @patch(
        "scripts.governance_gate.build_report",
        return_value={
            "pr_class": "implementation",
            "changed_paths": ["src/app.py"],
            "categories": ["implementation"],
            "allowed_categories": ["docs", "implementation"],
            "violations": [{"path": "src/app.py", "category": "implementation"}],
        },
    )
    @patch("scripts.governance_gate.git_changed_files", return_value=["src/app.py"])
    def test_scope_report_violation_still_blocks_ci(self, changed_files_mock, build_report_mock, validate_pr_preflight_mock) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "refs/heads/issue-57-demo"])

        self.assertEqual(exit_code, 1)
        changed_files_mock.assert_called_once()
        build_report_mock.assert_called_once_with("implementation", ["src/app.py"])
        validate_pr_preflight_mock.assert_not_called()

    @patch("scripts.governance_gate.validate_pr_preflight", return_value=["boom"])
    @patch("scripts.governance_gate.matching_exec_plan_for_issue", return_value={"item_key": "FR-0001-example", "item_type": "FR", "release": "v0.1.0", "sprint": "2026-S13"})
    @patch("scripts.governance_gate.build_report", return_value=SPEC_SCOPE_REPORT)
    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["docs/specs/FR-0001-example/spec.md"])
    @patch("scripts.governance_gate.git_current_branch", return_value="HEAD")
    def test_reuses_open_pr_preflight_contract_in_ci(
        self,
        current_branch_mock,
        changed_files_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
        build_report_mock,
        matching_exec_plan_mock,
        validate_pr_preflight_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "refs/heads/issue-57-demo"])

        self.assertEqual(exit_code, 1)
        current_branch_mock.assert_not_called()
        changed_files_mock.assert_called_once()
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()
        context_rules_mock.assert_called_once()
        build_report_mock.assert_called_once_with("spec", ["docs/specs/FR-0001-example/spec.md"])
        matching_exec_plan_mock.assert_called_once()
        validate_pr_preflight_mock.assert_called_once()

    @patch("scripts.governance_gate.validate_pr_preflight", return_value=["boom"])
    @patch("scripts.governance_gate.matching_exec_plan_for_issue", return_value={"item_key": "GOV-0028-harness-compat-migration", "item_type": "GOV", "release": "v0.2.0", "sprint": "2026-S15"})
    @patch("scripts.governance_gate.build_report", return_value={"pr_class": "docs", "changed_paths": ["vision.md"], "categories": ["docs"], "allowed_categories": ["docs"], "violations": []})
    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["vision.md"])
    @patch("scripts.governance_gate.git_current_branch", return_value="issue-57-demo")
    def test_docs_pr_still_reuses_open_pr_preflight_contract(
        self,
        current_branch_mock,
        changed_files_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
        build_report_mock,
        matching_exec_plan_mock,
        validate_pr_preflight_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "HEAD"])

        self.assertEqual(exit_code, 1)
        current_branch_mock.assert_called_once()
        changed_files_mock.assert_called_once()
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()
        context_rules_mock.assert_called_once()
        build_report_mock.assert_called_once_with("docs", ["vision.md"])
        matching_exec_plan_mock.assert_called_once()
        validate_pr_preflight_mock.assert_called_once()

    @patch("scripts.governance_gate.validate_pr_preflight", return_value=["boom"])
    @patch("scripts.governance_gate.matching_exec_plan_for_issue", return_value={"item_key": "FR-0001-example", "item_type": "FR", "release": "v0.1.0", "sprint": "2026-S13"})
    @patch("scripts.governance_gate.build_report", return_value={"pr_class": "spec", "changed_paths": ["docs/specs/FR-0001-example/contracts/README.md"], "categories": ["spec"], "allowed_categories": ["docs", "spec"], "violations": []})
    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["docs/specs/FR-0001-example/contracts/README.md"])
    @patch("scripts.governance_gate.git_current_branch", return_value="HEAD")
    def test_adjunct_only_spec_diff_still_fails_shared_preflight(
        self,
        current_branch_mock,
        changed_files_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
        build_report_mock,
        matching_exec_plan_mock,
        validate_pr_preflight_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "refs/heads/issue-57-demo"])

        self.assertEqual(exit_code, 1)
        current_branch_mock.assert_not_called()
        changed_files_mock.assert_called_once()
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()
        context_rules_mock.assert_called_once()
        build_report_mock.assert_called_once_with("spec", ["docs/specs/FR-0001-example/contracts/README.md"])
        matching_exec_plan_mock.assert_called_once()
        validate_pr_preflight_mock.assert_called_once()

    @patch("scripts.governance_gate.matching_exec_plan_for_issue")
    @patch("scripts.governance_gate.build_report", return_value=GOVERNANCE_SCOPE_REPORT)
    @patch("scripts.governance_gate.validate_context_rules", return_value=[])
    @patch("scripts.governance_gate.validate_context_repository", return_value=[])
    @patch("scripts.governance_gate.validate_workflow_repository", return_value=[])
    @patch("scripts.governance_gate.git_changed_files", return_value=["scripts/context_guard.py"])
    @patch("scripts.governance_gate.git_current_branch", return_value="HEAD")
    def test_rejects_diff_mode_when_issue_cannot_be_inferred(
        self,
        current_branch_mock,
        changed_files_mock,
        workflow_repo_mock,
        context_repo_mock,
        context_rules_mock,
        build_report_mock,
        matching_exec_plan_mock,
    ) -> None:
        exit_code = governance_gate.main(["--mode", "ci", "--base-ref", "origin/main", "--head-ref", "refs/pull/60/head"])

        self.assertEqual(exit_code, 1)
        current_branch_mock.assert_called_once()
        changed_files_mock.assert_called_once()
        workflow_repo_mock.assert_called_once()
        context_repo_mock.assert_called_once()
        context_rules_mock.assert_not_called()
        build_report_mock.assert_called_once_with("governance", ["scripts/context_guard.py"])
        matching_exec_plan_mock.assert_not_called()

    def test_infer_pr_class_treats_legacy_todo_path_as_spec_scope(self) -> None:
        self.assertEqual(
            governance_gate.infer_pr_class(["docs/specs/FR-0001-example/TODO.md"]),
            "spec",
        )

    def test_spec_scope_accepts_required_todo_updates(self) -> None:
        changed = [
            "docs/specs/FR-0001-example/spec.md",
            "docs/specs/FR-0001-example/TODO.md",
        ]
        self.assertEqual(governance_gate.infer_pr_class(changed), "spec")
        self.assertEqual(governance_gate.build_report("spec", changed)["violations"], [])

    def test_loom_carrier_paths_are_governance_scope(self) -> None:
        changed = [
            ".loom/bin/loom_flow.py",
            ".loom/companion/repo-interface.json",
            ".loom/bootstrap/init-result.json",
        ]
        self.assertEqual(governance_gate.infer_pr_class(changed), "governance")
        self.assertEqual(governance_gate.build_report("governance", changed)["violations"], [])

    def test_loom_carrier_guard_rejects_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            (root / ".loom/bootstrap/init-result.json").write_text("{invalid", encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/bootstrap/init-result.json"])

            self.assertTrue(any("Loom carrier JSON 无效" in error for error in errors))

    def test_loom_carrier_guard_is_static_and_accepts_valid_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/bin/loom_flow.py"])

            self.assertEqual(errors, [])

    def test_loom_carrier_guard_rejects_review_status_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/reviews/INIT-0001.json").read_text(encoding="utf-8"))
            payload["reviewed_validation_summary"] = "stale"
            (root / ".loom/reviews/INIT-0001.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/reviews/INIT-0001.json"])

            self.assertTrue(any("reviewed_validation_summary" in error for error in errors))

    def test_loom_carrier_guard_rejects_review_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/reviews/INIT-0001.json").read_text(encoding="utf-8"))
            payload["schema_version"] = "loom-review/v2"
            (root / ".loom/reviews/INIT-0001.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/reviews/INIT-0001.json"])

            self.assertTrue(any("schema_version 必须是 loom-review/v1" in error for error in errors))

    def test_loom_carrier_guard_rejects_spec_review_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/reviews/INIT-0001.spec.json").read_text(encoding="utf-8"))
            payload["schema_version"] = "loom-review/v2"
            (root / ".loom/reviews/INIT-0001.spec.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/reviews/INIT-0001.spec.json"])

            self.assertTrue(any("schema_version 必须是 loom-review/v1" in error for error in errors))

    def test_loom_carrier_guard_rejects_missing_status_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            (root / ".loom/status/current.md").write_text("- Item ID: INIT-0001\n", encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/status/current.md"])

            self.assertTrue(any("Loom status 缺少 `Latest Validation Summary`" in error for error in errors))

    def test_loom_carrier_guard_rejects_locator_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            status = (root / ".loom/status/current.md").read_text(encoding="utf-8")
            status += "- Review Entry: .loom/reviews/OTHER.json\n"
            (root / ".loom/status/current.md").write_text(status, encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/status/current.md"])

            self.assertTrue(any("Review Entry" in error and "不一致" in error for error in errors))

    def test_loom_carrier_guard_rejects_synchronized_wrong_locator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            for relative in (".loom/work-items/INIT-0001.md", ".loom/status/current.md"):
                path = root / relative
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "- Review Entry: .loom/reviews/INIT-0001.json",
                        "- Review Entry: .loom/reviews/OTHER.json",
                    ),
                    encoding="utf-8",
                )

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/status/current.md"])

            self.assertTrue(any("Review Entry" in error and "必须是" in error for error in errors))

    def test_loom_carrier_guard_rejects_missing_shadow_surface_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            (root / ".loom/shadow/admission-repo.json").unlink()

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/shadow/shadow-parity.json"])

            self.assertTrue(any("缺少 evidence" in error for error in errors))

    def test_loom_carrier_guard_rejects_shadow_parity_value_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/shadow/review-repo.json").read_text(encoding="utf-8"))
            payload["parity_value"] = "stale-review-parity"
            (root / ".loom/shadow/review-repo.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/shadow/review-repo.json"])

            self.assertTrue(any("parity_value 必须一致" in error for error in errors))

    def test_loom_carrier_guard_rejects_shadow_artifact_surface_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/shadow/shadow-parity.json").read_text(encoding="utf-8"))
            payload["surfaces"] = ["admission"]
            (root / ".loom/shadow/shadow-parity.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/shadow/shadow-parity.json"])

            self.assertTrue(any("surfaces 必须与 repo interop shadow_surfaces 完全一致" in error for error in errors))

    def test_loom_carrier_guard_rejects_synchronized_shadow_surface_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            interop = json.loads((root / ".loom/companion/interop.json").read_text(encoding="utf-8"))
            interop["shadow_surfaces"].pop("review")
            (root / ".loom/companion/interop.json").write_text(json.dumps(interop), encoding="utf-8")
            shadow = json.loads((root / ".loom/shadow/shadow-parity.json").read_text(encoding="utf-8"))
            shadow["surfaces"].remove("review")
            shadow["loom_sources"] = [source for source in shadow["loom_sources"] if "review-" not in source]
            shadow["repo_sources"] = [source for source in shadow["repo_sources"] if "review-" not in source]
            (root / ".loom/shadow/shadow-parity.json").write_text(json.dumps(shadow), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/companion/interop.json"])

            self.assertTrue(any("shadow_surfaces 必须固定为 admission/review/merge_ready/closeout" in error for error in errors))

    def test_loom_carrier_guard_rejects_shadow_artifact_schema_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/shadow/shadow-parity.json").read_text(encoding="utf-8"))
            payload["schema_version"] = "loom-shadow-parity-evidence/v2"
            (root / ".loom/shadow/shadow-parity.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/shadow/shadow-parity.json"])

            self.assertTrue(any("schema_version 必须是 loom-shadow-parity-evidence/v1" in error for error in errors))

    def test_loom_carrier_guard_rejects_shadow_source_locator_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/shadow/shadow-parity.json").read_text(encoding="utf-8"))
            payload["repo_sources"] = payload["repo_sources"][:-1]
            (root / ".loom/shadow/shadow-parity.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/shadow/shadow-parity.json"])

            self.assertTrue(any("sources 必须与 repo interop locators 完全一致" in error for error in errors))

    def test_loom_carrier_guard_rejects_shadow_source_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            (root / "WORKFLOW.md").write_text("# Workflow\n\nDrifted repo surface.\n", encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/shadow/admission-repo.json"])

            self.assertTrue(any("source hash 已漂移" in error for error in errors))

    def test_loom_carrier_guard_rejects_missing_bootstrap_inventory_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/bootstrap/manifest.json").read_text(encoding="utf-8"))
            payload["artifacts"] = [
                artifact
                for artifact in payload["artifacts"]
                if artifact["path"] != ".loom/companion/interop.json"
            ]
            (root / ".loom/bootstrap/manifest.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/bootstrap/manifest.json"])

            self.assertTrue(any("bootstrap manifest artifacts 缺少 `.loom/companion/interop.json`" in error for error in errors))

    def test_loom_carrier_guard_rejects_missing_active_item_inventory_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/bootstrap/init-result.json").read_text(encoding="utf-8"))
            payload["initial_artifacts"] = [
                artifact
                for artifact in payload["initial_artifacts"]
                if artifact["path"] != ".loom/specs/INIT-0001/spec.md"
            ]
            (root / ".loom/bootstrap/init-result.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/bootstrap/init-result.json"])

            self.assertTrue(any("init-result initial_artifacts 缺少 `.loom/specs/INIT-0001/spec.md`" in error for error in errors))

    def test_loom_carrier_guard_rejects_init_fact_chain_locator_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/bootstrap/init-result.json").read_text(encoding="utf-8"))
            payload["fact_chain"]["entry_points"]["work_item"] = "../outside.md"
            (root / ".loom/bootstrap/init-result.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/bootstrap/init-result.json"])

            self.assertTrue(any("fact_chain.entry_points.work_item 必须是 .loom/work-items/INIT-0001.md" in error for error in errors))

    def test_loom_carrier_guard_rejects_companion_locator_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/companion/manifest.json").read_text(encoding="utf-8"))
            payload["repo_interface"] = "../outside.json"
            (root / ".loom/companion/manifest.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/companion/manifest.json"])

            self.assertTrue(any("companion manifest `repo_interface` 必须是 .loom/companion/repo-interface.json" in error for error in errors))

    def test_loom_carrier_guard_rejects_repo_interface_companion_entry_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/companion/repo-interface.json").read_text(encoding="utf-8"))
            payload["companion_entry"] = "WORKFLOW.md"
            (root / ".loom/companion/repo-interface.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/companion/repo-interface.json"])

            self.assertTrue(any("repo interface `companion_entry` 必须是 .loom/companion/README.md" in error for error in errors))

    def test_loom_carrier_guard_rejects_missing_required_specialized_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/companion/repo-interface.json").read_text(encoding="utf-8"))
            payload["specialized_gates"] = [
                gate for gate in payload["specialized_gates"] if gate["id"] != "pr-guardian"
            ]
            (root / ".loom/companion/repo-interface.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/companion/repo-interface.json"])

            self.assertTrue(any("specialized_gates 缺少 required gate `pr-guardian`" in error for error in errors))

    def test_loom_carrier_guard_rejects_required_requirement_enforcement_downgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/companion/repo-interface.json").read_text(encoding="utf-8"))
            payload["repo_specific_requirements"]["review"][0]["enforcement"] = "advisory"
            (root / ".loom/companion/repo-interface.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/companion/repo-interface.json"])

            self.assertTrue(any("requirement `syvert-review-rubric` enforcement 必须是 blocking" in error for error in errors))

    def test_loom_carrier_guard_rejects_required_gate_type_reclassification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/companion/repo-interface.json").read_text(encoding="utf-8"))
            for gate in payload["specialized_gates"]:
                if gate["id"] == "pr-guardian":
                    gate["gate_type"] = "build"
            (root / ".loom/companion/repo-interface.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/companion/repo-interface.json"])

            self.assertTrue(any("specialized gate `pr-guardian` gate_type 必须是 merge_ready" in error for error in errors))

    def test_loom_carrier_guard_rejects_required_context_locator_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_loom_carrier(root)
            payload = json.loads((root / ".loom/companion/repo-interface.json").read_text(encoding="utf-8"))
            for field in payload["context_schema"]["fields"]:
                if field["id"] == "issue":
                    field["mapping_rule_locator"] = "WORKFLOW.md"
            (root / ".loom/companion/repo-interface.json").write_text(json.dumps(payload), encoding="utf-8")

            errors = governance_gate.validate_loom_carrier_repository(root, [".loom/companion/repo-interface.json"])

            self.assertTrue(any("context_schema field `issue` mapping_rule_locator 必须是 docs/process/delivery-funnel.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
