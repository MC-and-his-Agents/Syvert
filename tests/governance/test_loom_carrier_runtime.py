from __future__ import annotations

import json
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
LOOM_BIN = REPO_ROOT / ".loom/bin"


def load_loom_module(name: str):
    module_path = LOOM_BIN / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    sys.path.insert(0, str(LOOM_BIN))
    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            sys.path.remove(str(LOOM_BIN))
        except ValueError:
            pass


class LoomCarrierRuntimeTests(unittest.TestCase):
    def test_detect_github_repo_accepts_dotted_repo_names(self) -> None:
        governance_surface = load_loom_module("governance_surface")
        loom_flow = load_loom_module("loom_flow")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for module in (governance_surface, loom_flow):
                with patch.object(module, "git_remote_origin", return_value="git@github.com:owner/foo.bar.git"):
                    self.assertEqual(module.detect_github_repo(root), ("owner", "foo.bar"))

    def test_governance_surface_encodes_default_branch_api_path(self) -> None:
        governance_surface = load_loom_module("governance_surface")
        calls: list[str] = []

        def fake_gh_rest_json(root: Path, path: str):
            if path == "repos/owner/foo.bar":
                return {"full_name": "owner/foo.bar", "default_branch": "release/main"}, []
            raise AssertionError(path)

        def fake_gh_json(root: Path, args: list[str]):
            calls.append(args[-1])
            return {"protected": False}, []

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.object(governance_surface, "detect_github_repo", return_value=("owner", "foo.bar")):
                with patch.object(governance_surface, "gh_rest_json", side_effect=fake_gh_rest_json):
                    with patch.object(governance_surface, "gh_json", side_effect=fake_gh_json):
                        payload, errors = governance_surface.detect_github_control_plane(root)

        self.assertEqual(errors, [])
        self.assertEqual(payload["default_branch"], "release/main")
        self.assertIn("repos/owner/foo.bar/branches/release%2Fmain", calls)

    def test_contains_merged_commit_fetches_slash_target_branch(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        calls: list[list[str]] = []

        def fake_run_git(root: Path, args: list[str]):
            calls.append(args)

            class Result:
                returncode = 0

            return Result()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.object(loom_flow, "run_git", side_effect=fake_run_git):
                self.assertTrue(loom_flow.contains_merged_commit(root, "abc123", "release/main"))

        self.assertEqual(
            calls[0],
            ["fetch", "origin", "refs/heads/release/main:refs/remotes/origin/release/main"],
        )
        self.assertEqual(
            calls[1],
            ["merge-base", "--is-ancestor", "abc123", "refs/remotes/origin/release/main"],
        )

    def test_contains_merged_commit_blocks_when_fetch_fails(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        calls: list[list[str]] = []

        def fake_run_git(root: Path, args: list[str]):
            calls.append(args)

            class Result:
                returncode = 1

            return Result()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.object(loom_flow, "run_git", side_effect=fake_run_git):
                self.assertFalse(loom_flow.contains_merged_commit(root, "abc123", "release/main"))

        self.assertEqual(len(calls), 1)

    def test_runtime_state_rejects_install_layout_path_escape(self) -> None:
        runtime_state = load_loom_module("runtime_state")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "install-layout.json").write_text('{"required_paths":["../outside"]}', encoding="utf-8")
            payload, errors, _ = runtime_state._validate_install_layout(root)

        self.assertEqual(payload["status"], "block")
        self.assertTrue(any("must stay inside" in error for error in errors))

    def test_runtime_state_rejects_install_layout_path_escape_even_when_target_exists(self) -> None:
        runtime_state = load_loom_module("runtime_state")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside = root.parent / "outside"
            outside.write_text("ok\n", encoding="utf-8")
            (root / "install-layout.json").write_text('{"required_paths":["../outside"]}', encoding="utf-8")

            payload, errors, _ = runtime_state._validate_install_layout(root)

        self.assertEqual(payload["status"], "block")
        self.assertTrue(any("must stay inside" in error for error in errors))

    def test_runtime_state_rejects_registry_path_escape(self) -> None:
        runtime_state = load_loom_module("runtime_state")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "registry.json").write_text(
                '{"install_layout":"install-layout.json","upgrade_contract":"upgrade-contract.json","entries":[{"id":"x","executable":"/tmp/x","manifest":"../manifest"}]}',
                encoding="utf-8",
            )
            (root / "upgrade-contract.json").write_text('{"upgrade_policy":{"refresh_required":["layout_manifest"]}}', encoding="utf-8")
            payload, errors, _ = runtime_state._validate_registry_contract(root)

        self.assertEqual(payload["status"], "block")
        self.assertTrue(any("must stay inside" in error for error in errors))

    def test_runtime_state_rejects_registry_path_escape_even_when_targets_exist(self) -> None:
        runtime_state = load_loom_module("runtime_state")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outside_exec = root.parent / "outside-exec"
            outside_manifest = root.parent / "outside-manifest.json"
            outside_exec.write_text("#!/bin/sh\n", encoding="utf-8")
            outside_manifest.write_text("{}\n", encoding="utf-8")
            (root / "registry.json").write_text(
                '{"install_layout":"install-layout.json","upgrade_contract":"upgrade-contract.json","entries":[{"id":"x","executable":"../outside-exec","manifest":"../outside-manifest.json"}]}',
                encoding="utf-8",
            )
            (root / "upgrade-contract.json").write_text('{"upgrade_policy":{"refresh_required":["layout_manifest"]}}', encoding="utf-8")

            payload, errors, _ = runtime_state._validate_registry_contract(root)

        self.assertEqual(payload["status"], "block")
        self.assertTrue(any("must stay inside" in error for error in errors))

    def test_bootstrapped_runtime_wins_over_unrelated_source_repo_env(self) -> None:
        runtime_state = load_loom_module("runtime_state")
        with patch.dict(os.environ, {"LOOM_SOURCE_REPO_ROOT": "/tmp/not-loom"}, clear=False):
            payload = runtime_state.detect_runtime_state(
                str(LOOM_BIN / "runtime_state.py"),
                "loom-init",
                target_root=REPO_ROOT,
            )

        self.assertEqual(payload["carrier"], "bootstrapped-target-runtime")
        self.assertEqual(payload["result"], "pass")

    def test_bootstrapped_runtime_requires_manifest_sha256(self) -> None:
        runtime_state = load_loom_module("runtime_state")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime_root = root / ".loom/bin"
            manifest_path = root / ".loom/bootstrap/manifest.json"
            runtime_root.mkdir(parents=True)
            manifest_path.parent.mkdir(parents=True)
            artifacts = []
            for relative, source in runtime_state.EXPECTED_BOOTSTRAP_RUNTIME_SOURCES.items():
                runtime_file = runtime_root / Path(relative).name
                runtime_file.write_text("print('ok')\n", encoding="utf-8")
                artifacts.append({"path": relative, "kind": "loom-tool", "source": source})
            manifest_path.write_text(
                json.dumps({"schema_version": "loom-bootstrap-manifest/v1", "artifacts": artifacts}),
                encoding="utf-8",
            )

            _, errors, _ = runtime_state._validate_bootstrapped_runtime(str(runtime_root / "runtime_state.py"))

        self.assertTrue(any("must declare sha256 provenance" in error for error in errors))

    def test_spec_gate_does_not_fall_back_to_init_item_spec(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".loom/specs/INIT-0001").mkdir(parents=True)
            (root / ".loom/specs/INIT-0001/spec.md").write_text("bootstrap spec\n", encoding="utf-8")
            context = {
                "item_id": "WORK-0002",
                "target_root": root,
                "associated_artifacts": [".loom/specs/INIT-0001/spec.md"],
            }

            self.assertIsNone(loom_flow.formal_spec_path(context))
            self.assertEqual(
                loom_flow.spec_suite_paths(context),
                {
                    "spec": ".loom/specs/WORK-0002/spec.md",
                    "plan": ".loom/specs/WORK-0002/plan.md",
                    "implementation_contract": ".loom/specs/WORK-0002/implementation-contract.md",
                },
            )

    def test_governance_surface_uses_active_item_from_status(self) -> None:
        governance_surface = load_loom_module("governance_surface")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in (
                ".loom/work-items/WORK-0002.md",
                ".loom/progress/WORK-0002.md",
                ".loom/reviews/WORK-0002.json",
                ".loom/specs/WORK-0002/spec.md",
                ".loom/specs/WORK-0002/plan.md",
                ".loom/work-items/INIT-0001.md",
                ".loom/specs/INIT-0001/spec.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ok\n", encoding="utf-8")
            (root / ".loom/status").mkdir(parents=True, exist_ok=True)
            (root / ".loom/status/current.md").write_text("- Item ID: WORK-0002\n", encoding="utf-8")
            (root / ".loom/bootstrap").mkdir(parents=True, exist_ok=True)
            (root / ".loom/bootstrap/init-result.json").write_text(
                json.dumps(
                    {
                        "fact_chain": {
                            "entry_points": {
                                "current_item_id": "WORK-0002",
                                "work_item": ".loom/work-items/WORK-0002.md",
                                "recovery_entry": ".loom/progress/WORK-0002.md",
                                "status_surface": ".loom/status/current.md",
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            summary = governance_surface.detect_carrier_summary(
                root,
                repository_mode="complex-existing",
                planning_mode=False,
            )
            execution_entry = governance_surface.detect_execution_entry(
                root,
                "active",
                bootstrap_mode=True,
                active_item_id="WORK-0002",
            )
            merge_surface = governance_surface.detect_review_merge_surface(
                root,
                "active",
                bootstrap_mode=True,
                active_item_id="WORK-0002",
            )

            self.assertEqual(summary["work_item"]["locator"], ".loom/work-items/WORK-0002.md")
            self.assertEqual(summary["spec_path"]["locator"], ".loom/specs/WORK-0002/spec.md")
            self.assertIn("--item WORK-0002", execution_entry)
            self.assertIn("--item WORK-0002", merge_surface["merge_surface"])

    def test_bootstrap_write_rejects_output_path_escape(self) -> None:
        loom_init = load_loom_module("loom_init")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()

            with self.assertRaises(RuntimeError):
                loom_init.resolve_output_path(root, "../outside.json")

    def test_bootstrap_cli_rejects_output_path_escape(self) -> None:
        loom_init = load_loom_module("loom_init")
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir) / "repo"
            outside_path = Path(temp_dir) / "outside.json"
            target_root.mkdir()

            exit_code = loom_init.main(
                [
                    "bootstrap",
                    "--target",
                    str(target_root),
                    "--output",
                    "../outside.json",
                    "--write",
                ]
            )

            self.assertEqual(exit_code, 2)
            self.assertFalse(outside_path.exists())

    def test_fact_chain_rejects_entry_point_path_escape(self) -> None:
        fact_chain_support = load_loom_module("fact_chain_support")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            (root / ".loom/bootstrap").mkdir(parents=True)
            (root / ".loom/bootstrap/init-result.json").write_text(
                json.dumps(
                    {
                        "schema_version": "loom-init-output/v1",
                        "fact_chain": {
                            "read_entry": "python3 .loom/bin/loom_init.py fact-chain --target .",
                            "mode": "work-item + recovery-entry + derived status-surface",
                            "entry_points": {
                                "current_item_id": "INIT-0001",
                                "work_item": "../outside.md",
                                "recovery_entry": ".loom/progress/INIT-0001.md",
                                "status_surface": ".loom/status/current.md",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            _, errors = fact_chain_support.inspect_fact_chain(root)

        self.assertTrue(any("must stay within the target root" in error for error in errors))

    def test_work_item_create_rejects_recovery_entry_escape(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            (root / ".loom/bootstrap").mkdir(parents=True)
            (root / ".loom/bootstrap/init-result.json").write_text("{}", encoding="utf-8")
            outside = root.parent / "outside.md"

            exit_code = loom_flow.handle_work_item(
                loom_flow.parse_args(
                    [
                        "work-item",
                        "create",
                        "--target",
                        str(root),
                        "--item",
                        "INIT-0002",
                        "--goal",
                        "Goal",
                        "--scope",
                        "Scope",
                        "--execution-path",
                        "governance/test",
                        "--workspace-entry",
                        ".",
                        "--recovery-entry",
                        "../outside.md",
                        "--validation-entry",
                        "python3 .loom/bin/loom_init.py verify --target .",
                        "--closing-condition",
                        "Done",
                    ]
                )
            )

            self.assertEqual(exit_code, 1)
            self.assertFalse(outside.exists())

    def test_review_record_rejects_review_file_escape(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            captured: dict[str, object] = {}
            args = loom_flow.parse_args(
                [
                    "review",
                    "record",
                    "--target",
                    str(root),
                    "--item",
                    "INIT-0001",
                    "--review-file",
                    "../outside.json",
                    "--decision",
                    "allow",
                    "--kind",
                    "general_review",
                    "--summary",
                    "ok",
                    "--reviewer",
                    "codex",
                ]
            )
            context = {
                "item_id": "INIT-0001",
                "review_entry": ".loom/reviews/INIT-0001.json",
                "latest_validation_summary": "ok",
                "report": {
                    "fact_chain": {
                        "entry_points": {
                            "work_item": ".loom/work-items/INIT-0001.md",
                            "recovery_entry": ".loom/progress/INIT-0001.md",
                            "status_surface": ".loom/status/current.md",
                        }
                    }
                },
            }

            def capture(payload):
                captured.update(payload)
                return 1

            with patch.object(loom_flow, "load_context", return_value=(context, [])):
                with patch.object(loom_flow, "checkpoint_payload", return_value={"result": "pass", "missing_inputs": [], "fallback_to": None, "summary": "ok"}):
                    with patch.object(loom_flow, "spec_review_gate_payload", return_value={"result": "pass", "missing_inputs": [], "fallback_to": None}):
                        with patch.object(loom_flow, "emit", side_effect=capture):
                            exit_code = loom_flow.handle_review(args)

            self.assertEqual(exit_code, 1)
            self.assertEqual(captured.get("result"), "block")
            self.assertIn("review artifact path", " ".join(captured.get("missing_inputs", [])))

    def test_governance_surface_rejects_companion_locator_escape(self) -> None:
        governance_surface = load_loom_module("governance_surface")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside.json"
            (root / ".loom/companion").mkdir(parents=True)
            outside.write_text("{}", encoding="utf-8")
            (root / ".loom/companion/manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "loom-repo-companion-manifest/v1",
                        "companion_entry": ".loom/companion/README.md",
                        "repo_interface": "../outside.json",
                    }
                ),
                encoding="utf-8",
            )
            (root / ".loom/companion/README.md").write_text("# Companion\n", encoding="utf-8")

            payload, errors = governance_surface.detect_repo_interface(root)

            self.assertEqual(payload["availability"], "incomplete")
            self.assertTrue(any("must stay within the repository root" in error for error in errors))

    def test_governance_surface_rejects_shadow_locator_escape(self) -> None:
        governance_surface = load_loom_module("governance_surface")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside.json"
            outside.write_text("{}", encoding="utf-8")

            errors = governance_surface.validate_shadow_surface(
                root=root,
                surface="review",
                entry={
                    "summary": "review parity",
                    "loom_locator": ".loom/shadow/review-loom.json",
                    "repo_locator": "../outside.json",
                },
            )

            self.assertTrue(any("must stay within the repository root" in error for error in errors))

    def test_shadow_source_hashes_require_source_files(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / ".loom/shadow/review-repo.json"
            evidence_path.parent.mkdir(parents=True)
            (root / "WORKFLOW.md").write_text("ok\n", encoding="utf-8")
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": "loom-shadow-surface-evidence/v1",
                        "surface": "review",
                        "side": "repo",
                        "parity_value": "ok",
                        "source_semantics": "review parity requires aligned review evidence",
                        "source_sha256": {"WORKFLOW.md": loom_flow.sha256_file(root / "WORKFLOW.md")},
                    }
                ),
                encoding="utf-8",
            )

            value, error = loom_flow.normalized_shadow_value(evidence_path, target_root=root)

            self.assertIn("review parity requires aligned review evidence", value["normalized_value"])
            self.assertIn("must declare non-empty `source_files`", error)

    def test_shadow_source_hashes_require_exact_source_set(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            evidence_path = root / ".loom/shadow/review-repo.json"
            evidence_path.parent.mkdir(parents=True)
            (root / "WORKFLOW.md").write_text("ok\n", encoding="utf-8")
            (root / "code_review.md").write_text("review\n", encoding="utf-8")
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": "loom-shadow-surface-evidence/v1",
                        "surface": "review",
                        "side": "repo",
                        "parity_value": "ok",
                        "evidence_body": {
                            "authority": "guardian + workflow",
                            "decision_rule": "blocking review inputs must align",
                        },
                        "source_files": ["WORKFLOW.md", "code_review.md"],
                        "source_sha256": {"WORKFLOW.md": loom_flow.sha256_file(root / "WORKFLOW.md")},
                    }
                ),
                encoding="utf-8",
            )

            value, error = loom_flow.normalized_shadow_value(evidence_path, target_root=root)

            self.assertIn("guardian + workflow", value["normalized_value"])
            self.assertIn("source_files and source_sha256 keys must match exactly", error)

    def test_shadow_parity_blocks_semantics_drift_even_when_parity_value_matches(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".loom/companion").mkdir(parents=True)
            (root / ".loom/shadow").mkdir(parents=True)
            (root / "WORKFLOW.md").write_text("workflow\n", encoding="utf-8")
            (root / ".loom/spec.md").write_text("spec\n", encoding="utf-8")
            (root / ".loom/companion/interop.json").write_text(
                json.dumps(
                    {
                        "schema_version": "loom-repo-interop/v1",
                        "host_adapters": [],
                        "repo_native_carriers": [],
                        "shadow_surfaces": {
                            "review": {
                                "summary": "review parity",
                                "loom_locator": ".loom/shadow/review-loom.json",
                                "repo_locator": ".loom/shadow/review-repo.json",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            common_payload = {
                "schema_version": "loom-shadow-surface-evidence/v1",
                "surface": "review",
                "parity_value": "review-parity-v1",
            }
            (root / ".loom/shadow/review-loom.json").write_text(
                json.dumps(
                    {
                        **common_payload,
                        "side": "loom",
                        "source_semantics": "review parity requires spec review and linked review evidence before merge decisions.",
                        "source_files": [".loom/spec.md"],
                        "source_sha256": {".loom/spec.md": loom_flow.sha256_file(root / ".loom/spec.md")},
                    }
                ),
                encoding="utf-8",
            )
            (root / ".loom/shadow/review-repo.json").write_text(
                json.dumps(
                    {
                        **common_payload,
                        "side": "repo",
                        "source_semantics": "review parity allows merge without spec review as long as guardian returns allow.",
                        "source_files": ["WORKFLOW.md"],
                        "source_sha256": {"WORKFLOW.md": loom_flow.sha256_file(root / "WORKFLOW.md")},
                    }
                ),
                encoding="utf-8",
            )

            report = loom_flow.shadow_parity_report(
                {
                    "availability": "present",
                    "contract": {"locator": ".loom/companion/interop.json"},
                },
                target_root=root,
                surface="review",
            )

            self.assertEqual(report["result"], "mismatch")
            self.assertEqual(report["classification"], "drift")

    def test_shadow_parity_rejects_external_shadow_locators(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = loom_flow.shadow_parity_report(
                {
                    "availability": "present",
                    "contract": {"locator": "../outside-interop.json"},
                },
                target_root=root,
                surface="review",
            )

            self.assertEqual(report["result"], "unreadable")
            self.assertTrue(any("repo interop contract" in item for item in report["missing_inputs"]))

    def test_shadow_parity_rejects_declared_repo_external_surface_locator(self) -> None:
        loom_flow = load_loom_module("loom_flow")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".loom/companion").mkdir(parents=True)
            interop = {
                "schema_version": "loom-repo-interop/v1",
                "host_adapters": [],
                "repo_native_carriers": [],
                "shadow_surfaces": {
                    "review": {
                        "summary": "review parity",
                        "loom_locator": "../outside-loom.json",
                        "repo_locator": "../outside-repo.json",
                    }
                },
            }
            (root / ".loom/companion/interop.json").write_text(json.dumps(interop), encoding="utf-8")

            report = loom_flow.shadow_parity_report(
                {
                    "availability": "present",
                    "contract": {"locator": ".loom/companion/interop.json"},
                },
                target_root=root,
                surface="review",
            )

            self.assertEqual(report["result"], "unreadable")
            missing_details = report.get("missing_details")
            self.assertIsInstance(missing_details, list)
            self.assertTrue(
                any(
                    isinstance(detail, dict)
                    and detail.get("category") == "path_boundary"
                    and detail.get("kind") == "repo_locator_escape"
                    and detail.get("scope") == "repository_root"
                    and detail.get("label") == "shadow surface `review` repo_locator"
                    and detail.get("locator") == "../outside-repo.json"
                    for detail in missing_details
                )
            )

    def test_loom_check_requires_adversarial_adoption_evidence(self) -> None:
        loom_check = load_loom_module("loom_check")
        self.assertIn(
            "docs/evidence/validations/validation-syvert-adversarial-adoption-fixture.md",
            loom_check.CORE_DOCS,
        )


if __name__ == "__main__":
    unittest.main()
