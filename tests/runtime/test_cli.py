from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
import tempfile
from unittest import mock

from syvert.cli import main
from syvert.task_record import (
    TaskRecordContractError,
    TaskRequestSnapshot,
    create_task_record,
    start_task_record,
    task_record_to_dict,
)
from syvert.task_record_store import LocalTaskRecordStore


REPO_ROOT = Path(__file__).resolve().parents[2]


class SuccessfulAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
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


class PlatformFailureAdapter:
    adapter_key = "stub"
    supported_capabilities = frozenset({"content_detail"})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})

    def execute(self, request):
        from syvert.runtime import PlatformAdapterError

        raise PlatformAdapterError(
            code="platform_broken",
            message="boom",
            details={"reason": "bad"},
        )


class BrokenWriteStream(io.StringIO):
    def write(self, s: str) -> int:
        raise BrokenPipeError("forced-broken-pipe")


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._task_record_store_dir = tempfile.TemporaryDirectory()
        self._task_record_store_patcher = mock.patch.dict(
            os.environ,
            {"SYVERT_TASK_RECORD_STORE_DIR": self._task_record_store_dir.name},
            clear=False,
        )
        self._task_record_store_patcher.start()

    def tearDown(self) -> None:
        self._task_record_store_patcher.stop()
        self._task_record_store_dir.cleanup()
        super().tearDown()

    def subprocess_env(self) -> dict[str, str]:
        return {
            "PYTHONPATH": str(REPO_ROOT),
            "SYVERT_TASK_RECORD_STORE_DIR": self._task_record_store_dir.name,
        }

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
        env = self.subprocess_env()
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
        self.assertEqual(payload["error"]["category"], "invalid_input")
        self.assertEqual(payload["error"]["code"], "invalid_cli_arguments")

    def test_cli_parse_failure_preserves_adapter_key_from_equals_syntax(self) -> None:
        env = self.subprocess_env()
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
        env = self.subprocess_env()
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
        env = self.subprocess_env()
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

    def test_cli_persists_task_record_through_default_store_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = {
                "PYTHONPATH": str(REPO_ROOT),
                "SYVERT_TASK_RECORD_STORE_DIR": temp_dir,
            }
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
                    "https://example.com/posts/persisted-1",
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
            persisted = LocalTaskRecordStore(Path(temp_dir)).load(payload["task_id"])
            self.assertEqual(persisted.task_id, payload["task_id"])
            self.assertEqual(persisted.status, "succeeded")

    def test_run_subcommand_writes_success_envelope_to_stdout(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "run",
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/run-1",
            ],
            adapters={"stub": SuccessfulAdapter()},
            stdout=stdout,
            stderr=stderr,
            task_id_factory=lambda: "task-cli-run-001",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-run-001")
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["adapter_key"], "stub")

    def test_query_subcommand_returns_persisted_success_record(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        legacy_stdout = io.StringIO()
        legacy_stderr = io.StringIO()

        legacy_exit_code = main(
            [
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/query-success-1",
            ],
            adapters={"stub": SuccessfulAdapter()},
            stdout=legacy_stdout,
            stderr=legacy_stderr,
            task_id_factory=lambda: "task-cli-query-success-1",
        )

        self.assertEqual(legacy_exit_code, 0, legacy_stderr.getvalue())
        expected_payload = task_record_to_dict(store.load("task-cli-query-success-1"))

        query_stdout = io.StringIO()
        query_stderr = io.StringIO()
        query_exit_code = main(
            ["query", "--task-id", "task-cli-query-success-1"],
            stdout=query_stdout,
            stderr=query_stderr,
        )

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stderr.getvalue(), "")
        self.assertEqual(json.loads(query_stdout.getvalue()), expected_payload)

    def test_query_subcommand_returns_accepted_record(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        accepted = create_task_record(
            "task-cli-query-accepted-1",
            TaskRequestSnapshot(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/query-accepted-1",
                collection_mode="hybrid",
            ),
        )
        store.write(accepted)

        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = main(
            ["query", "--task-id", "task-cli-query-accepted-1"],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue()), task_record_to_dict(accepted))

    def test_query_subcommand_returns_running_record(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        accepted = create_task_record(
            "task-cli-query-running-1",
            TaskRequestSnapshot(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/query-running-1",
                collection_mode="hybrid",
            ),
        )
        running = start_task_record(accepted)
        store.write(accepted)
        store.write(running)

        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = main(
            ["query", "--task-id", "task-cli-query-running-1"],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue()), task_record_to_dict(running))

    def test_query_subcommand_returns_persisted_failed_record(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        legacy_stdout = io.StringIO()
        legacy_stderr = io.StringIO()

        legacy_exit_code = main(
            [
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/query-failed-1",
            ],
            adapters={"stub": PlatformFailureAdapter()},
            stdout=legacy_stdout,
            stderr=legacy_stderr,
            task_id_factory=lambda: "task-cli-query-failed-1",
        )

        self.assertEqual(legacy_exit_code, 1)
        expected_payload = task_record_to_dict(store.load("task-cli-query-failed-1"))

        query_stdout = io.StringIO()
        query_stderr = io.StringIO()
        query_exit_code = main(
            ["query", "--task-id", "task-cli-query-failed-1"],
            stdout=query_stdout,
            stderr=query_stderr,
        )

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stderr.getvalue(), "")
        self.assertEqual(json.loads(query_stdout.getvalue()), expected_payload)

    def test_query_subcommand_returns_invalid_cli_arguments_when_task_id_missing(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            ["query"],
            stdout=stdout,
            stderr=stderr,
            task_id_factory=lambda: "task-cli-query-parse-failure",
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["task_id"], "task-cli-query-parse-failure")
        self.assertEqual(payload["adapter_key"], "")
        self.assertEqual(payload["capability"], "")
        self.assertEqual(payload["error"]["category"], "invalid_input")
        self.assertEqual(payload["error"]["code"], "invalid_cli_arguments")

    def test_query_subcommand_parse_failure_preserves_recoverable_task_id(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            ["query", "--task-id", "task-cli-query-recoverable-1", "--unknown"],
            stdout=stdout,
            stderr=stderr,
            task_id_factory=lambda: "task-cli-query-fallback-should-not-be-used",
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["task_id"], "task-cli-query-recoverable-1")
        self.assertEqual(payload["adapter_key"], "")
        self.assertEqual(payload["capability"], "")
        self.assertEqual(payload["error"]["category"], "invalid_input")
        self.assertEqual(payload["error"]["code"], "invalid_cli_arguments")

    def test_query_subcommand_parse_failure_returns_invalid_task_id_when_fallback_task_id_generation_fails(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            ["query"],
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
        self.assertEqual(payload["adapter_key"], "")
        self.assertEqual(payload["capability"], "")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "invalid_task_id")

    def test_query_subcommand_returns_not_found_for_unknown_task_id(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            ["query", "--task-id", "task-cli-query-missing-1"],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["task_id"], "task-cli-query-missing-1")
        self.assertEqual(payload["adapter_key"], "")
        self.assertEqual(payload["capability"], "")
        self.assertEqual(payload["error"]["category"], "invalid_input")
        self.assertEqual(payload["error"]["code"], "task_record_not_found")

    def test_query_subcommand_returns_unavailable_for_invalid_marker(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        legacy_stdout = io.StringIO()
        legacy_stderr = io.StringIO()

        legacy_exit_code = main(
            [
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/query-invalid-marker-1",
            ],
            adapters={"stub": SuccessfulAdapter()},
            stdout=legacy_stdout,
            stderr=legacy_stderr,
            task_id_factory=lambda: "task-cli-query-invalid-marker-1",
        )
        self.assertEqual(legacy_exit_code, 0, legacy_stderr.getvalue())
        store.mark_invalid(
            "task-cli-query-invalid-marker-1",
            stage="completion",
            reason="forced-invalid-marker",
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = main(
            ["query", "--task-id", "task-cli-query-invalid-marker-1"],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-query-invalid-marker-1")
        self.assertEqual(payload["adapter_key"], "")
        self.assertEqual(payload["capability"], "")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "task_record_unavailable")

    def test_query_subcommand_returns_unavailable_for_invalid_json_record(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        store.root.mkdir(parents=True, exist_ok=True)
        store.record_path("task-cli-query-bad-json-1").write_text("{bad json", encoding="utf-8")

        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = main(
            ["query", "--task-id", "task-cli-query-bad-json-1"],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-query-bad-json-1")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "task_record_unavailable")

    def test_query_subcommand_returns_unavailable_for_contract_invalid_record(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        store.root.mkdir(parents=True, exist_ok=True)
        invalid_payload = {
            "schema_version": "v0.3.0",
            "task_id": "task-cli-query-bad-contract-1",
            "request": {
                "adapter_key": "stub",
                "capability": "content_detail_by_url",
                "target_type": "url",
                "target_value": "https://example.com/posts/query-bad-contract-1",
                "collection_mode": "hybrid",
            },
            "status": "accepted",
            "created_at": "2026-04-18T10:00:00Z",
            "updated_at": "2026-04-18T10:00:00Z",
            "terminal_at": None,
            "result": None,
            "logs": [],
        }
        store.record_path("task-cli-query-bad-contract-1").write_text(
            json.dumps(invalid_payload, ensure_ascii=False),
            encoding="utf-8",
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = main(
            ["query", "--task-id", "task-cli-query-bad-contract-1"],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-query-bad-contract-1")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "task_record_unavailable")

    def test_query_subcommand_uses_record_context_when_loaded_record_fails_to_serialize(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        accepted = create_task_record(
            "task-cli-query-serialize-failure-1",
            TaskRequestSnapshot(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/query-serialize-failure-1",
                collection_mode="hybrid",
            ),
        )
        store.write(accepted)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch(
            "syvert.cli.task_record_to_dict",
            side_effect=TaskRecordContractError("forced-serialization-error"),
        ):
            exit_code = main(
                ["query", "--task-id", "task-cli-query-serialize-failure-1"],
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-query-serialize-failure-1")
        self.assertEqual(payload["adapter_key"], "stub")
        self.assertEqual(payload["capability"], "content_detail_by_url")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "task_record_unavailable")

    def test_query_subcommand_uses_record_context_when_loaded_record_cannot_be_written_to_stdout(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        accepted = create_task_record(
            "task-cli-query-write-failure-1",
            TaskRequestSnapshot(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/query-write-failure-1",
                collection_mode="hybrid",
            ),
        )
        store.write(accepted)

        stdout = BrokenWriteStream()
        stderr = io.StringIO()
        exit_code = main(
            ["query", "--task-id", "task-cli-query-write-failure-1"],
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-query-write-failure-1")
        self.assertEqual(payload["adapter_key"], "stub")
        self.assertEqual(payload["capability"], "content_detail_by_url")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "task_record_unavailable")

    def test_query_subcommand_returns_unavailable_when_store_root_is_missing(self) -> None:
        missing_root = Path(self._task_record_store_dir.name) / "missing-root"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch.dict(os.environ, {"SYVERT_TASK_RECORD_STORE_DIR": str(missing_root)}, clear=False):
            exit_code = main(
                ["query", "--task-id", "task-cli-query-missing-root-1"],
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["task_id"], "task-cli-query-missing-root-1")
        self.assertEqual(payload["adapter_key"], "")
        self.assertEqual(payload["capability"], "")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "task_record_unavailable")

    def test_run_subcommand_persists_record_that_query_reads_from_shared_store(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        run_stdout = io.StringIO()
        run_stderr = io.StringIO()

        run_exit_code = main(
            [
                "run",
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/shared-run-1",
            ],
            adapters={"stub": SuccessfulAdapter()},
            stdout=run_stdout,
            stderr=run_stderr,
            task_id_factory=lambda: "task-cli-shared-run-1",
        )

        self.assertEqual(run_exit_code, 0, run_stderr.getvalue())
        expected_payload = task_record_to_dict(store.load("task-cli-shared-run-1"))

        query_stdout = io.StringIO()
        query_stderr = io.StringIO()
        query_exit_code = main(
            ["query", "--task-id", "task-cli-shared-run-1"],
            stdout=query_stdout,
            stderr=query_stderr,
        )

        self.assertEqual(query_exit_code, 0)
        self.assertEqual(query_stderr.getvalue(), "")
        self.assertEqual(json.loads(query_stdout.getvalue()), expected_payload)

    def test_run_subcommand_and_legacy_entrypoint_persist_equivalent_durable_truth(self) -> None:
        store = LocalTaskRecordStore(Path(self._task_record_store_dir.name))
        legacy_stdout = io.StringIO()
        legacy_stderr = io.StringIO()

        legacy_exit_code = main(
            [
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/shared-legacy-1",
            ],
            adapters={"stub": SuccessfulAdapter()},
            stdout=legacy_stdout,
            stderr=legacy_stderr,
            task_id_factory=lambda: "task-cli-shared-legacy-1",
        )

        self.assertEqual(legacy_exit_code, 0, legacy_stderr.getvalue())
        legacy_record_payload = task_record_to_dict(store.load("task-cli-shared-legacy-1"))

        run_stdout = io.StringIO()
        run_stderr = io.StringIO()
        run_exit_code = main(
            [
                "run",
                "--adapter",
                "stub",
                "--capability",
                "content_detail_by_url",
                "--url",
                "https://example.com/posts/shared-legacy-1",
            ],
            adapters={"stub": SuccessfulAdapter()},
            stdout=run_stdout,
            stderr=run_stderr,
            task_id_factory=lambda: "task-cli-shared-run-equivalent-1",
        )

        self.assertEqual(run_exit_code, 0, run_stderr.getvalue())
        run_record_payload = task_record_to_dict(store.load("task-cli-shared-run-equivalent-1"))

        legacy_record_payload["task_id"] = "normalized-task-id"
        run_record_payload["task_id"] = "normalized-task-id"
        legacy_record_payload["result"]["envelope"]["task_id"] = "normalized-task-id"
        run_record_payload["result"]["envelope"]["task_id"] = "normalized-task-id"

        self.assertEqual(run_record_payload["request"], legacy_record_payload["request"])
        self.assertEqual(run_record_payload["status"], legacy_record_payload["status"])
        self.assertEqual(run_record_payload["result"], legacy_record_payload["result"])

    def test_query_subcommand_reads_loaded_record_via_shared_store_and_shared_serializer(self) -> None:
        record = create_task_record(
            "task-cli-shared-store-serializer-1",
            TaskRequestSnapshot(
                adapter_key="stub",
                capability="content_detail_by_url",
                target_type="url",
                target_value="https://example.com/posts/shared-store-serializer-1",
                collection_mode="hybrid",
            ),
        )
        expected_payload = {
            "schema_version": "v0.3.0",
            "task_id": "task-cli-shared-store-serializer-1",
            "request": {"adapter_key": "stub"},
            "status": "accepted",
        }
        store = mock.Mock()
        store.load.return_value = record

        stdout = io.StringIO()
        stderr = io.StringIO()
        shadow_payload = Path(self._task_record_store_dir.name) / "shadow-payload.json"
        shadow_payload.write_text(json.dumps({"shadow": "payload"}), encoding="utf-8")
        with mock.patch("syvert.cli.default_task_record_store", return_value=store), mock.patch(
            "syvert.cli.validate_query_store_root",
            return_value=None,
        ), mock.patch("syvert.cli.task_record_to_dict", return_value=expected_payload) as serializer, mock.patch(
            "builtins.open",
            side_effect=AssertionError("unexpected_file_open"),
        ), mock.patch(
            "pathlib.Path.open",
            side_effect=AssertionError("unexpected_path_open"),
        ), mock.patch(
            "pathlib.Path.read_text",
            side_effect=AssertionError("unexpected_path_read_text"),
        ), mock.patch(
            "pathlib.Path.read_bytes",
            side_effect=AssertionError("unexpected_path_read_bytes"),
        ), mock.patch(
            "pathlib.Path.exists",
            side_effect=AssertionError("unexpected_path_exists"),
        ):
            exit_code = main(
                ["query", "--task-id", "task-cli-shared-store-serializer-1"],
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        store.load.assert_called_once_with("task-cli-shared-store-serializer-1")
        serializer.assert_called_once_with(record)
        self.assertEqual(json.loads(stdout.getvalue()), expected_payload)

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

    def test_cli_shared_builder_fails_closed_for_duplicate_adapter_keys(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch("syvert.adapters.build_xhs_adapters", return_value={"dup": SuccessfulAdapter()}), mock.patch(
            "syvert.adapters.build_douyin_adapters",
            return_value={"dup": SuccessfulAdapter()},
        ):
            exit_code = main(
                [
                    "--adapter",
                    "dup",
                    "--capability",
                    "content_detail_by_url",
                    "--url",
                    "https://example.com/posts/1",
                    "--adapter-module",
                    "syvert.adapters:build_adapters",
                ],
                stdout=stdout,
                stderr=stderr,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error"]["category"], "runtime_contract")
        self.assertEqual(payload["error"]["code"], "invalid_adapter_registry")

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
        self.assertEqual(payload["error"]["category"], "unsupported")

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
        self.assertEqual(payload["error"]["category"], "unsupported")
        self.assertEqual(payload["error"]["code"], "adapter_not_found")

    def test_cli_loader_failure_returns_machine_readable_failure(self) -> None:
        env = self.subprocess_env()
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
        env = self.subprocess_env()
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
