from __future__ import annotations

import json
import importlib.util
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
        self.assertTrue(any("inside the installed skills root" in error for error in errors))

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
        self.assertTrue(any("inside the installed skills root" in error for error in errors))

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

            summary = governance_surface.detect_carrier_summary(
                root,
                repository_mode="complex-existing",
                planning_mode=False,
            )
            execution_entry = governance_surface.detect_execution_entry(root, "active", bootstrap_mode=True)
            merge_surface = governance_surface.detect_review_merge_surface(root, "active", bootstrap_mode=True)

            self.assertEqual(summary["work_item"]["locator"], ".loom/work-items/WORK-0002.md")
            self.assertEqual(summary["spec_path"]["locator"], ".loom/specs/WORK-0002/spec.md")
            self.assertIn("--item WORK-0002", execution_entry)
            self.assertIn("--item WORK-0002", merge_surface["merge_surface"])

    def test_bootstrap_write_rejects_symlinked_carrier_escape(self) -> None:
        loom_init = load_loom_module("loom_init")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside"
            root.mkdir()
            outside.mkdir()
            (root / ".loom").symlink_to(outside, target_is_directory=True)

            with self.assertRaises(RuntimeError):
                loom_init.assert_write_path_inside_target(root, root / ".loom/README.md")

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
                        "source_sha256": {"WORKFLOW.md": loom_flow.sha256_file(root / "WORKFLOW.md")},
                    }
                ),
                encoding="utf-8",
            )

            value, error = loom_flow.normalized_shadow_value(evidence_path, target_root=root)

            self.assertIsNone(value)
            self.assertIn("invalid source_files", error)

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
                        "source_files": ["WORKFLOW.md", "code_review.md"],
                        "source_sha256": {"WORKFLOW.md": loom_flow.sha256_file(root / "WORKFLOW.md")},
                    }
                ),
                encoding="utf-8",
            )

            value, error = loom_flow.normalized_shadow_value(evidence_path, target_root=root)

            self.assertIsNone(value)
            self.assertIn("source_files must exactly match source_sha256 keys", error)


if __name__ == "__main__":
    unittest.main()
