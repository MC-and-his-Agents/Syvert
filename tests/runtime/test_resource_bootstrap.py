from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from syvert.resource_lifecycle import AcquireRequest, ResourceBundle, ReleaseRequest, acquire, release
from syvert.resource_bootstrap import (
    bootstrap_resource_store,
    build_bootstrap_records,
    canonicalize_account_material,
    load_account_material,
)
from syvert.resource_lifecycle_store import LocalResourceLifecycleStore


REPO_ROOT = Path(__file__).resolve().parents[2]


class ResourceBootstrapTests(unittest.TestCase):
    def test_canonicalize_xhs_account_material_preserves_runtime_contract(self) -> None:
        material = canonicalize_account_material(
            adapter_key="xhs",
            material={
                "cookies": "a=1; b=2",
                "user_agent": "Mozilla/5.0 TestAgent",
                "sign_base_url": "http://127.0.0.1:8000",
                "timeout_seconds": "5",
            },
        )

        self.assertEqual(
            material,
            {
                "cookies": "a=1; b=2",
                "user_agent": "Mozilla/5.0 TestAgent",
                "sign_base_url": "http://127.0.0.1:8000",
                "timeout_seconds": 5,
                "managed_adapter_key": "xhs",
            },
        )

    def test_load_account_material_from_legacy_douyin_session_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = Path(temp_dir) / "douyin.session.json"
            session_file.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "verify_fp": "verify-1",
                        "ms_token": "ms-token-1",
                        "webid": "webid-1",
                        "sign_base_url": "http://127.0.0.1:8000",
                        "timeout_seconds": 5,
                    }
                ),
                encoding="utf-8",
            )

            material = load_account_material(
                adapter_key="douyin",
                account_session_file=session_file,
            )

        self.assertEqual(material["cookies"], "a=1; b=2")
        self.assertEqual(material["user_agent"], "Mozilla/5.0 TestAgent")
        self.assertEqual(material["verify_fp"], "verify-1")
        self.assertEqual(material["ms_token"], "ms-token-1")
        self.assertEqual(material["webid"], "webid-1")
        self.assertEqual(material["sign_base_url"], "http://127.0.0.1:8000")
        self.assertEqual(material["timeout_seconds"], 5)
        self.assertEqual(material["managed_adapter_key"], "douyin")

    def test_build_bootstrap_records_validates_account_material(self) -> None:
        with self.assertRaisesRegex(ValueError, "cookies"):
            build_bootstrap_records(
                adapter_key="xhs",
                account_resource_id="xhs-account-main",
                account_material={"user_agent": "Mozilla/5.0 TestAgent"},
                proxy_resource_id="proxy-main",
                proxy_material={"proxy_endpoint": "http://proxy-001"},
            )

    def test_bootstrap_resource_store_seeds_managed_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LocalResourceLifecycleStore(Path(temp_dir) / "resource-lifecycle.json")
            records = build_bootstrap_records(
                adapter_key="xhs",
                account_resource_id="xhs-account-main",
                account_material={
                    "cookies": "a=1; b=2",
                    "user_agent": "Mozilla/5.0 TestAgent",
                    "sign_base_url": "http://127.0.0.1:8000",
                    "timeout_seconds": 5,
                },
                proxy_resource_id="proxy-main",
                proxy_material={"proxy_endpoint": "http://proxy-001"},
            )

            seeded = bootstrap_resource_store(store=store, records=records)

            self.assertEqual({record.resource_id for record in seeded}, {"xhs-account-main", "proxy-main"})
            snapshot = store.load_snapshot()

        self.assertEqual(snapshot.revision, 1)
        self.assertEqual({record.resource_id for record in snapshot.resources}, {"xhs-account-main", "proxy-main"})

    def test_bootstrap_script_seeds_store_from_legacy_session_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "resource-lifecycle.json"
            session_file = Path(temp_dir) / "xhs.session.json"
            proxy_file = Path(temp_dir) / "proxy.json"
            session_file.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "sign_base_url": "http://127.0.0.1:8000",
                        "timeout_seconds": 5,
                    }
                ),
                encoding="utf-8",
            )
            proxy_file.write_text(json.dumps({"proxy_endpoint": "http://proxy-001"}), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "syvert.resource_bootstrap_cli",
                    "--adapter",
                    "xhs",
                    "--account-resource-id",
                    "xhs-account-main",
                    "--account-session-file",
                    str(session_file),
                    "--proxy-resource-id",
                    "proxy-main",
                    "--proxy-material-file",
                    str(proxy_file),
                    "--store-file",
                    str(store_file),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["store_file"], str(store_file))
            self.assertEqual(payload["adapter_key"], "xhs")
            self.assertEqual(payload["seeded_resource_ids"], ["proxy-main", "xhs-account-main"])

            snapshot = LocalResourceLifecycleStore(store_file).load_snapshot()

        self.assertEqual(snapshot.revision, 1)
        resources = {record.resource_id: record for record in snapshot.resources}
        self.assertEqual(resources["xhs-account-main"].material["cookies"], "a=1; b=2")
        self.assertEqual(resources["proxy-main"].material["proxy_endpoint"], "http://proxy-001")

    def test_bootstrap_cli_keeps_adapter_accounts_isolated_in_shared_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store_file = Path(temp_dir) / "resource-lifecycle.json"
            xhs_session_file = Path(temp_dir) / "xhs.session.json"
            douyin_session_file = Path(temp_dir) / "douyin.session.json"
            proxy_file = Path(temp_dir) / "proxy.json"
            xhs_session_file.write_text(
                json.dumps(
                    {
                        "cookies": "xhs=1",
                        "user_agent": "Mozilla/5.0 XhsAgent",
                        "sign_base_url": "http://127.0.0.1:8000",
                        "timeout_seconds": 5,
                    }
                ),
                encoding="utf-8",
            )
            douyin_session_file.write_text(
                json.dumps(
                    {
                        "cookies": "douyin=1",
                        "user_agent": "Mozilla/5.0 DouyinAgent",
                        "verify_fp": "verify-1",
                        "ms_token": "ms-token-1",
                        "webid": "webid-1",
                        "sign_base_url": "http://127.0.0.1:8000",
                        "timeout_seconds": 5,
                    }
                ),
                encoding="utf-8",
            )
            proxy_file.write_text(json.dumps({"proxy_endpoint": "http://proxy-001"}), encoding="utf-8")

            for adapter_key, resource_id, session_file in (
                ("xhs", "xhs-account-main", xhs_session_file),
                ("douyin", "douyin-account-main", douyin_session_file),
            ):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "syvert.resource_bootstrap_cli",
                        "--adapter",
                        adapter_key,
                        "--account-resource-id",
                        resource_id,
                        "--account-session-file",
                        str(session_file),
                        "--proxy-resource-id",
                        "proxy-main",
                        "--proxy-material-file",
                        str(proxy_file),
                        "--store-file",
                        str(store_file),
                    ],
                    cwd=REPO_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            store = LocalResourceLifecycleStore(store_file)

            xhs_bundle = acquire(
                AcquireRequest(
                    task_id="task-xhs",
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    requested_slots=("account", "proxy"),
                ),
                store,
                "task-xhs",
            )
            self.assertIsInstance(xhs_bundle, ResourceBundle)
            assert isinstance(xhs_bundle, ResourceBundle)
            assert xhs_bundle.account is not None
            self.assertEqual(xhs_bundle.account.resource_id, "xhs-account-main")
            release(
                ReleaseRequest(
                    task_id="task-xhs",
                    lease_id=xhs_bundle.lease_id,
                    target_status_after_release="AVAILABLE",
                    reason="test",
                ),
                store,
                "task-xhs",
            )

            douyin_bundle = acquire(
                AcquireRequest(
                    task_id="task-douyin",
                    adapter_key="douyin",
                    capability="content_detail_by_url",
                    requested_slots=("account", "proxy"),
                ),
                store,
                "task-douyin",
            )
            self.assertIsInstance(douyin_bundle, ResourceBundle)
            assert isinstance(douyin_bundle, ResourceBundle)
            assert douyin_bundle.account is not None
            self.assertEqual(douyin_bundle.account.resource_id, "douyin-account-main")
