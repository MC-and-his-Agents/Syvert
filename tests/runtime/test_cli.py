from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

from syvert.cli import main


REPO_ROOT = Path(__file__).resolve().parents[2]


class SuccessfulAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail_by_url"})

    def execute(self, request):
        url = request.input.url
        return {
            "raw": {"id": "raw-cli-1", "url": url},
            "normalized": {
                "platform": "stub",
                "content_id": "content-cli-1",
                "content_type": "unknown",
                "canonical_url": url,
                "title": "",
                "body_text": "",
                "published_at": None,
                "author": {
                    "author_id": None,
                    "display_name": None,
                    "avatar_url": None,
                },
                "stats": {
                    "like_count": None,
                    "comment_count": None,
                    "share_count": None,
                    "collect_count": None,
                },
                "media": {
                    "cover_url": None,
                    "video_url": None,
                    "image_urls": [],
                },
            },
        }


class CliTests(unittest.TestCase):
    def test_cli_wrapper_help_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "syvert.cli", "--help"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)

    def test_cli_module_path_can_load_adapter_source(self) -> None:
        env = dict(**{"PYTHONPATH": str(REPO_ROOT)})
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "syvert.cli",
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/1",
                "--adapter-module",
                "tests.runtime.adapter_fixtures:build_adapters",
            ],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["adapter_key"], "stub")

    def test_main_writes_success_envelope_to_stdout(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/1",
            ],
            adapters={"stub": SuccessfulAdapter()},
            stdout=stdout,
            stderr=stderr,
            task_id_factory=lambda: "task-cli-001",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-001")
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["adapter_key"], "stub")
        self.assertEqual(payload["capability"], "content_detail_by_url")

    def test_main_returns_non_zero_for_failed_envelope(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "--adapter",
                "missing",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/1",
            ],
            adapters={},
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["category"], "runtime_contract")

    def test_cli_loader_failure_returns_machine_readable_failure(self) -> None:
        env = dict(**{"PYTHONPATH": str(REPO_ROOT)})
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "syvert.cli",
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/1",
                "--adapter-module",
                "tests.runtime.adapter_fixtures:missing_builder",
            ],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stderr)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "adapter_loader_error")

    def test_loader_failure_uses_injected_task_id_factory(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/1",
                "--adapter-module",
                "tests.runtime.adapter_fixtures:missing_builder",
            ],
            stdout=stdout,
            stderr=stderr,
            task_id_factory=lambda: "task-cli-loader-failure",
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-loader-failure")
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["code"], "adapter_loader_error")

    def test_loader_failure_fails_closed_when_task_id_factory_raises(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/1",
                "--adapter-module",
                "tests.runtime.adapter_fixtures:missing_builder",
            ],
            stdout=stdout,
            stderr=stderr,
            task_id_factory=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "failed")
        self.assertIsInstance(payload["task_id"], str)
        self.assertTrue(payload["task_id"])
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "invalid_task_id")

    def test_cli_fails_closed_when_success_envelope_is_not_json_serializable(self) -> None:
        env = dict(**{"PYTHONPATH": str(REPO_ROOT)})
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "syvert.cli",
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/1",
                "--adapter-module",
                "tests.runtime.adapter_fixtures:build_unserializable_adapters",
            ],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        payload = json.loads(result.stderr)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "envelope_not_json_serializable")


if __name__ == "__main__":
    unittest.main()
