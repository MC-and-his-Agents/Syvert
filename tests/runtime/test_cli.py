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
        return {
            "raw": {"id": "raw-cli-1", "url": request.input_url},
            "normalized": {
                "platform": "stub",
                "content_id": "content-cli-1",
                "content_type": "unknown",
                "canonical_url": request.input_url,
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


if __name__ == "__main__":
    unittest.main()
