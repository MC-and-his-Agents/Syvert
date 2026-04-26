from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
