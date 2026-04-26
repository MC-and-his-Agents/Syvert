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
                "result": "pass",
                "surfaces": list(surfaces),
                "loom_sources": loom_sources,
                "repo_sources": repo_sources,
            }
        ),
        encoding="utf-8",
    )


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


if __name__ == "__main__":
    unittest.main()
