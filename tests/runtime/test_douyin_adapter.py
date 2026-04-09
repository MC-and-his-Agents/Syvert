from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
from threading import Thread
from typing import Any
import unittest
from unittest import mock

from syvert.runtime import PlatformAdapterError, TaskInput, TaskRequest, execute_task


def build_douyin_aweme_detail(
    *,
    aweme_id: str = "7580570616932224282",
    desc: str = "抖音正文",
    preview_title: str = "抖音标题",
    create_time: Any = 1764989142,
    digg_count: Any = 2871,
    comment_count: Any = 220,
    share_count: Any = 972,
    collect_count: Any = 3220,
    video_url: str = "https://cdn.example/video.mp4",
    cover_url: str = "https://cdn.example/cover.jpg",
) -> dict[str, Any]:
    return {
        "aweme_id": aweme_id,
        "aweme_type": 0,
        "desc": desc,
        "preview_title": preview_title,
        "create_time": create_time,
        "statistics": {
            "digg_count": digg_count,
            "comment_count": comment_count,
            "share_count": share_count,
            "collect_count": collect_count,
        },
        "author": {
            "uid": "author-1",
            "nickname": "抖音作者",
            "avatar_thumb": {
                "url_list": [cover_url],
            },
        },
        "video": {
            "play_addr_h264": {"url_list": [video_url]},
            "cover": {"url_list": [cover_url]},
        },
    }


class DouyinAdapterTests(unittest.TestCase):
    def test_parse_douyin_detail_url_extracts_aweme_id_from_canonical_url(self) -> None:
        from syvert.adapters.douyin import parse_douyin_detail_url

        parsed = parse_douyin_detail_url("https://www.douyin.com/video/7580570616932224282")

        self.assertEqual(parsed.aweme_id, "7580570616932224282")
        self.assertEqual(parsed.canonical_url, "https://www.douyin.com/video/7580570616932224282")

    def test_parse_douyin_detail_url_extracts_aweme_id_from_share_url(self) -> None:
        from syvert.adapters.douyin import parse_douyin_detail_url

        parsed = parse_douyin_detail_url(
            "https://www.iesdouyin.com/share/video/7580570616932224282/?region=CN&mid=mid-1"
        )

        self.assertEqual(parsed.aweme_id, "7580570616932224282")
        self.assertEqual(parsed.canonical_url, "https://www.douyin.com/video/7580570616932224282")

    def test_parse_douyin_detail_url_rejects_short_link_until_resolver_exists(self) -> None:
        from syvert.adapters.douyin import parse_douyin_detail_url

        with self.assertRaises(PlatformAdapterError) as raised:
            parse_douyin_detail_url("https://v.douyin.com/abcd1234/")

        self.assertEqual(raised.exception.code, "invalid_douyin_url")

    def test_load_session_config_requires_verify_fields(self) -> None:
        from syvert.adapters.douyin import load_session_config

        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "douyin.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1",
                        "user_agent": "Mozilla/5.0",
                        "ms_token": "ms-token",
                        "webid": "webid-1",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(PlatformAdapterError) as raised:
                load_session_config(session_path)

        self.assertEqual(raised.exception.code, "douyin_session_missing")

    def test_default_sign_transport_rejects_failed_sign_payload(self) -> None:
        from syvert.adapters.douyin import default_sign_transport

        with mock.patch(
            "syvert.adapters.douyin.post_json",
            return_value={"isok": False, "msg": "sign failed", "data": None},
        ):
            with self.assertRaises(PlatformAdapterError) as raised:
                default_sign_transport(
                    "http://127.0.0.1:8000",
                    {
                        "uri": "/aweme/v1/web/aweme/detail/",
                        "query_params": "aweme_id=7580570616932224282",
                        "user_agent": "Mozilla/5.0",
                        "cookies": "a=1",
                    },
                    5,
                )

        self.assertEqual(raised.exception.code, "douyin_sign_unavailable")

    def test_normalize_detail_response_rejects_success_without_aweme_detail(self) -> None:
        from syvert.adapters.douyin import normalize_detail_response

        with self.assertRaises(PlatformAdapterError) as raised:
            normalize_detail_response({"status_code": 0})

        self.assertEqual(raised.exception.code, "douyin_content_not_found")

    def test_douyin_adapter_execute_builds_success_payload_from_api_responses(self) -> None:
        from syvert.adapters.douyin import DouyinAdapter

        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "douyin.session.json"
            session_path.write_text(
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
            sign_calls: list[dict[str, Any]] = []
            detail_calls: list[dict[str, Any]] = []
            adapter = DouyinAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: sign_calls.append(
                    {"base_url": base_url, "payload": payload, "timeout_seconds": timeout_seconds}
                )
                or {"a_bogus": "signed-1"},
                detail_transport=lambda **kwargs: detail_calls.append(kwargs)
                or {"status_code": 0, "aweme_detail": build_douyin_aweme_detail()},
            )

            payload = adapter.execute(
                TaskRequest(
                    adapter_key="douyin",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://www.douyin.com/video/7580570616932224282"),
                )
            )

        self.assertEqual(payload["raw"]["aweme_detail"]["aweme_id"], "7580570616932224282")
        self.assertEqual(payload["normalized"]["platform"], "douyin")
        self.assertEqual(payload["normalized"]["content_id"], "7580570616932224282")
        self.assertEqual(payload["normalized"]["content_type"], "video")
        self.assertEqual(payload["normalized"]["canonical_url"], "https://www.douyin.com/video/7580570616932224282")
        self.assertEqual(payload["normalized"]["title"], "抖音标题")
        self.assertEqual(payload["normalized"]["body_text"], "抖音正文")
        self.assertEqual(payload["normalized"]["stats"]["like_count"], 2871)
        self.assertEqual(payload["normalized"]["media"]["video_url"], "https://cdn.example/video.mp4")
        self.assertEqual(sign_calls[0]["payload"]["uri"], "/aweme/v1/web/aweme/detail/")
        self.assertIn("verifyFp=verify-1", sign_calls[0]["payload"]["query_params"])
        self.assertEqual(detail_calls[0]["params"]["a_bogus"], "signed-1")

    def test_douyin_adapter_coerces_invalid_numeric_fields_to_null(self) -> None:
        from syvert.adapters.douyin import DouyinAdapter

        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "douyin.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "verify_fp": "verify-1",
                        "ms_token": "ms-token-1",
                        "webid": "webid-1",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = DouyinAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
                detail_transport=lambda **kwargs: {
                    "status_code": 0,
                    "aweme_detail": build_douyin_aweme_detail(
                        create_time="not-a-number",
                        digg_count="nan",
                        comment_count=True,
                        share_count="5",
                        collect_count=None,
                    ),
                },
            )

            payload = adapter.execute(
                TaskRequest(
                    adapter_key="douyin",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://www.douyin.com/video/7580570616932224282"),
                )
            )

        self.assertEqual(payload["normalized"]["published_at"], None)
        self.assertEqual(payload["normalized"]["stats"]["like_count"], None)
        self.assertEqual(payload["normalized"]["stats"]["comment_count"], None)
        self.assertEqual(payload["normalized"]["stats"]["share_count"], 5)
        self.assertEqual(payload["normalized"]["stats"]["collect_count"], None)

    def test_douyin_adapter_maps_structured_detail_failure_to_platform_error(self) -> None:
        from syvert.adapters.douyin import DouyinAdapter

        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "douyin.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "verify_fp": "verify-1",
                        "ms_token": "ms-token-1",
                        "webid": "webid-1",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = DouyinAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
                detail_transport=lambda **kwargs: {
                    "status_code": 2190008,
                    "status_msg": "content missing",
                },
            )

            with self.assertRaises(PlatformAdapterError) as raised:
                adapter.execute(
                    TaskRequest(
                        adapter_key="douyin",
                        capability="content_detail_by_url",
                        input=TaskInput(url="https://www.douyin.com/video/7580570616932224282"),
                    )
                )

        self.assertEqual(raised.exception.code, "douyin_detail_request_failed")
        self.assertEqual(raised.exception.details["platform_code"], 2190008)

    def test_douyin_adapter_falls_back_to_browser_page_state_when_detail_fails(self) -> None:
        from syvert.adapters.douyin import DouyinAdapter

        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "douyin.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "verify_fp": "verify-1",
                        "ms_token": "ms-token-1",
                        "webid": "webid-1",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = DouyinAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
                detail_transport=lambda **kwargs: (_ for _ in ()).throw(
                    PlatformAdapterError(
                        code="douyin_detail_request_failed",
                        message="detail failed",
                        details={"reason": "blocked"},
                    )
                ),
                page_state_transport=lambda **kwargs: {
                    "SSR_RENDER_DATA": {
                        "aweme_detail": build_douyin_aweme_detail(desc="浏览器回退正文")
                    }
                },
            )

            payload = adapter.execute(
                TaskRequest(
                    adapter_key="douyin",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://www.douyin.com/video/7580570616932224282"),
                )
            )

        self.assertEqual(payload["normalized"]["body_text"], "浏览器回退正文")
        self.assertEqual(payload["raw"]["SSR_RENDER_DATA"]["aweme_detail"]["aweme_id"], "7580570616932224282")

    def test_douyin_adapter_preserves_original_error_when_browser_page_state_misses_target(self) -> None:
        from syvert.adapters.douyin import DouyinAdapter

        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "douyin.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "verify_fp": "verify-1",
                        "ms_token": "ms-token-1",
                        "webid": "webid-1",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = DouyinAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
                detail_transport=lambda **kwargs: (_ for _ in ()).throw(
                    PlatformAdapterError(
                        code="douyin_detail_request_failed",
                        message="detail failed",
                        details={"reason": "blocked"},
                    )
                ),
                page_state_transport=lambda **kwargs: {
                    "SSR_RENDER_DATA": {
                        "aweme_detail": build_douyin_aweme_detail(aweme_id="other-aweme")
                    }
                },
            )

            with self.assertRaises(PlatformAdapterError) as raised:
                adapter.execute(
                    TaskRequest(
                        adapter_key="douyin",
                        capability="content_detail_by_url",
                        input=TaskInput(url="https://www.douyin.com/video/7580570616932224282"),
                    )
                )

        self.assertEqual(raised.exception.code, "douyin_detail_request_failed")

    def test_douyin_adapter_accepts_browser_detail_recovery_payload(self) -> None:
        from syvert.adapters.douyin import DouyinAdapter

        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "douyin.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "verify_fp": "verify-1",
                        "ms_token": "ms-token-1",
                        "webid": "webid-1",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = DouyinAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {"a_bogus": "signed-1"},
                detail_transport=lambda **kwargs: (_ for _ in ()).throw(
                    PlatformAdapterError(
                        code="douyin_detail_request_failed",
                        message="detail failed",
                        details={"reason": "blocked"},
                    )
                ),
                page_state_transport=lambda **kwargs: {
                    "SSR_RENDER_DATA": {},
                    "RENDER_DATA": {},
                    "SIGI_STATE": {},
                    "AWEME_DETAIL": build_douyin_aweme_detail(desc="浏览器请求回退正文"),
                },
            )

            payload = adapter.execute(
                TaskRequest(
                    adapter_key="douyin",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://www.douyin.com/video/7580570616932224282"),
                )
            )

        self.assertEqual(payload["normalized"]["body_text"], "浏览器请求回退正文")

    def test_execute_task_returns_platform_failure_envelope_for_douyin_platform_errors(self) -> None:
        from syvert.adapters.douyin import DouyinAdapter

        adapter = DouyinAdapter(
            session_provider=lambda path: (_ for _ in ()).throw(
                PlatformAdapterError(
                    code="douyin_session_missing",
                    message="抖音会话文件不存在",
                    details={"session_path": str(path)},
                )
            )
        )

        envelope = execute_task(
            TaskRequest(
                adapter_key="douyin",
                capability="content_detail_by_url",
                input=TaskInput(url="https://www.douyin.com/video/7580570616932224282"),
            ),
            adapters={"douyin": adapter},
            task_id_factory=lambda: "task-douyin-001",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "douyin_session_missing")
