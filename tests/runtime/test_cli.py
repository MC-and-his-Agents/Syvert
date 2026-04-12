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
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

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

    def test_cli_fails_closed_for_missing_required_arguments(self) -> None:
        env = dict(**{"PYTHONPATH": str(REPO_ROOT)})
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "syvert.cli",
                "--adapter",
                "stub",
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
        self.assertEqual(payload["adapter_key"], "stub")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "invalid_cli_arguments")

    def test_cli_parse_failure_preserves_adapter_key_from_equals_syntax(self) -> None:
        env = dict(**{"PYTHONPATH": str(REPO_ROOT)})
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "syvert.cli",
                "--adapter=stub",
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
        self.assertEqual(payload["adapter_key"], "stub")
        self.assertEqual(payload["error"]["code"], "invalid_cli_arguments")

    def test_cli_parse_failure_does_not_consume_next_flag_as_adapter_value(self) -> None:
        env = dict(**{"PYTHONPATH": str(REPO_ROOT)})
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "syvert.cli",
                "--adapter",
                "--capability",
                "content_detail_by_url",
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
        self.assertEqual(payload["adapter_key"], "")
        self.assertEqual(payload["capability"], "content_detail_by_url")
        self.assertEqual(payload["error"]["code"], "invalid_cli_arguments")

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

    def test_cli_module_path_can_load_shared_adapter_registry(self) -> None:
        import tempfile
        from unittest import mock

        from tests.runtime.test_douyin_adapter import build_douyin_aweme_detail

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread

        handler_state: dict[str, list[dict[str, object]]] = {"sign_calls": [], "detail_calls": []}

        class RequestHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                if self.path == "/signsrv/v1/douyin/sign":
                    handler_state["sign_calls"].append(payload)
                    response = {"isok": True, "data": {"a_bogus": "signed-cli-1"}}
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))

            def do_GET(self) -> None:
                if self.path.startswith("/aweme/v1/web/aweme/detail/"):
                    handler_state["detail_calls"].append({"path": self.path})
                    response = {"status_code": 0, "aweme_detail": build_douyin_aweme_detail()}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp_home:
                session_path = Path(temp_home) / "douyin.session.json"
                session_path.write_text(
                    json.dumps(
                        {
                            "cookies": "a=1; b=2",
                            "user_agent": "Mozilla/5.0 TestAgent",
                            "verify_fp": "verify-cli-1",
                            "ms_token": "ms-token-cli-1",
                            "webid": "webid-cli-1",
                            "sign_base_url": f"http://127.0.0.1:{server.server_port}",
                            "timeout_seconds": 5,
                        }
                    ),
                    encoding="utf-8",
                )
                stdout = io.StringIO()
                stderr = io.StringIO()
                with mock.patch("syvert.adapters.douyin.DEFAULT_DOUYIN_SESSION_PATH", session_path), mock.patch(
                    "syvert.adapters.douyin.DOUYIN_API_BASE_URL",
                    f"http://127.0.0.1:{server.server_port}",
                ):
                    exit_code = main(
                        [
                            "--adapter",
                            "douyin",
                            "--capability",
                            "content_detail_by_url",
                            "--url",
                            "https://www.douyin.com/video/7580570616932224282",
                            "--adapter-module",
                            "syvert.adapters:build_adapters",
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

        self.assertEqual(exit_code, 0, stderr.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["adapter_key"], "douyin")
        self.assertEqual(payload["normalized"]["platform"], "douyin")
        self.assertEqual(payload["normalized"]["canonical_url"], "https://www.douyin.com/video/7580570616932224282")
        self.assertEqual(len(handler_state["sign_calls"]), 1)
        self.assertEqual(len(handler_state["detail_calls"]), 1)

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

    def test_injected_empty_adapter_registry_is_authoritative(self) -> None:
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
                "tests.runtime.adapter_fixtures:build_adapters",
            ],
            adapters={},
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["code"], "adapter_not_found")

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
