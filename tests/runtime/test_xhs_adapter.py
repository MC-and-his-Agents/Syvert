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

from syvert.cli import main
from syvert.runtime import TaskInput, TaskRequest, execute_task

from syvert.adapters.xhs import XhsAdapter, parse_xhs_detail_url


class XhsAdapterTests(unittest.TestCase):
    def test_parse_xhs_detail_url_extracts_note_id_and_xsec_values(self) -> None:
        parsed = parse_xhs_detail_url(
            "https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"
            "?xsec_token=token-1&xsec_source=pc_search"
        )

        self.assertEqual(parsed.note_id, "66fad51c000000001b0224b8")
        self.assertEqual(parsed.xsec_token, "token-1")
        self.assertEqual(parsed.xsec_source, "pc_search")

    def test_parse_xhs_detail_url_accepts_explore_url_without_query(self) -> None:
        parsed = parse_xhs_detail_url("https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8")

        self.assertEqual(parsed.note_id, "66fad51c000000001b0224b8")
        self.assertEqual(parsed.xsec_token, "")
        self.assertEqual(parsed.xsec_source, "")

    def test_parse_xhs_detail_url_rejects_xhslink_until_short_link_resolution_exists(self) -> None:
        with self.assertRaises(Exception) as raised:
            parse_xhs_detail_url("https://www.xhslink.com/explore/66fad51c000000001b0224b8")
        self.assertEqual(raised.exception.code, "invalid_xhs_url")

    def test_parse_xhs_detail_url_rejects_non_xhs_url(self) -> None:
        with self.assertRaises(Exception) as raised:
            parse_xhs_detail_url("https://example.com/posts/1")
        self.assertEqual(raised.exception.code, "invalid_xhs_url")

    def test_xhs_adapter_execute_builds_success_payload_from_api_responses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "xhs.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "sign_base_url": "http://127.0.0.1:8000",
                        "timeout_seconds": 7,
                    }
                ),
                encoding="utf-8",
            )
            sign_requests: list[dict[str, Any]] = []
            detail_requests: list[dict[str, Any]] = []

            def sign_transport(base_url: str, payload: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
                sign_requests.append(
                    {
                        "base_url": base_url,
                        "payload": payload,
                        "timeout_seconds": timeout_seconds,
                    }
                )
                return {
                    "x_s": "signed-x-s",
                    "x_t": "signed-x-t",
                    "x_s_common": "signed-x-s-common",
                    "x_b3_traceid": "trace-1",
                }

            def detail_transport(
                *,
                url: str,
                headers: dict[str, str],
                body: dict[str, Any],
                timeout_seconds: int,
            ) -> dict[str, Any]:
                detail_requests.append(
                    {
                        "url": url,
                        "headers": headers,
                        "body": body,
                        "timeout_seconds": timeout_seconds,
                    }
                )
                return {
                    "items": [
                        {
                            "note_card": {
                                "note_id": "66fad51c000000001b0224b8",
                                "type": "video",
                                "title": "测试标题",
                                "desc": "测试正文",
                                "time": 1712304300,
                                "user": {
                                    "user_id": "user-1",
                                    "nickname": "作者甲",
                                    "avatar": "https://cdn.example/avatar.jpg",
                                },
                                "interact_info": {
                                    "liked_count": "11",
                                    "comment_count": "12",
                                    "share_count": "13",
                                    "collected_count": "14",
                                },
                                "image_list": [
                                    {"url_default": "https://cdn.example/image-1.jpg"},
                                    {"url_default": "https://cdn.example/image-2.jpg"},
                                ],
                                "video": {
                                    "consumer": {
                                        "origin_video_key": "video-key-1",
                                    }
                                },
                                "cover": {
                                    "url_default": "https://cdn.example/cover.jpg",
                                },
                            }
                        }
                    ]
                }

            adapter = XhsAdapter(
                session_path=session_path,
                sign_transport=sign_transport,
                detail_transport=detail_transport,
            )

            payload = adapter.execute(
                TaskRequest(
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    input=TaskInput(
                        url=(
                            "https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"
                            "?xsec_token=token-1&xsec_source=pc_search"
                        )
                    ),
                )
            )

        self.assertEqual(len(sign_requests), 1)
        self.assertEqual(sign_requests[0]["base_url"], "http://127.0.0.1:8000")
        self.assertEqual(sign_requests[0]["payload"]["uri"], "/api/sns/web/v1/feed")
        self.assertEqual(sign_requests[0]["payload"]["cookies"], "a=1; b=2")
        self.assertEqual(sign_requests[0]["timeout_seconds"], 7)
        self.assertEqual(len(detail_requests), 1)
        self.assertEqual(detail_requests[0]["url"], "https://edith.xiaohongshu.com/api/sns/web/v1/feed")
        self.assertEqual(detail_requests[0]["timeout_seconds"], 7)
        self.assertEqual(detail_requests[0]["body"]["source_note_id"], "66fad51c000000001b0224b8")
        self.assertEqual(detail_requests[0]["body"]["xsec_token"], "token-1")
        self.assertEqual(detail_requests[0]["body"]["xsec_source"], "pc_search")
        self.assertEqual(detail_requests[0]["headers"]["X-s"], "signed-x-s")
        self.assertEqual(detail_requests[0]["headers"]["X-t"], "signed-x-t")
        self.assertEqual(detail_requests[0]["headers"]["x-s-common"], "signed-x-s-common")
        self.assertEqual(detail_requests[0]["headers"]["X-B3-Traceid"], "trace-1")
        self.assertEqual(detail_requests[0]["headers"]["cookie"], "a=1; b=2")
        self.assertEqual(payload["raw"]["items"][0]["note_card"]["note_id"], "66fad51c000000001b0224b8")
        self.assertEqual(payload["normalized"]["platform"], "xhs")
        self.assertEqual(payload["normalized"]["content_id"], "66fad51c000000001b0224b8")
        self.assertEqual(payload["normalized"]["content_type"], "video")
        self.assertEqual(
            payload["normalized"]["canonical_url"],
            "https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8",
        )
        self.assertEqual(payload["normalized"]["title"], "测试标题")
        self.assertEqual(payload["normalized"]["body_text"], "测试正文")
        self.assertEqual(payload["normalized"]["published_at"], "2024-04-05T08:05:00Z")
        self.assertEqual(payload["normalized"]["author"]["author_id"], "user-1")
        self.assertEqual(payload["normalized"]["author"]["display_name"], "作者甲")
        self.assertEqual(payload["normalized"]["author"]["avatar_url"], "https://cdn.example/avatar.jpg")
        self.assertEqual(payload["normalized"]["stats"]["like_count"], 11)
        self.assertEqual(payload["normalized"]["stats"]["comment_count"], 12)
        self.assertEqual(payload["normalized"]["stats"]["share_count"], 13)
        self.assertEqual(payload["normalized"]["stats"]["collect_count"], 14)
        self.assertEqual(payload["normalized"]["media"]["cover_url"], "https://cdn.example/cover.jpg")
        self.assertEqual(
            payload["normalized"]["media"]["video_url"],
            "https://sns-video-bd.xhscdn.com/video-key-1",
        )
        self.assertEqual(
            payload["normalized"]["media"]["image_urls"],
            [
                "https://cdn.example/image-1.jpg",
                "https://cdn.example/image-2.jpg",
            ],
        )
        self.assertNotIn("xsec_token", payload["raw"])

    def test_xhs_adapter_maps_structured_detail_failure_to_platform_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "xhs.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = XhsAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {
                    "x_s": "signed-x-s",
                    "x_t": "signed-x-t",
                    "x_s_common": "signed-x-s-common",
                    "x_b3_traceid": "trace-1",
                },
                detail_transport=lambda **kwargs: {
                    "success": False,
                    "code": 300013,
                    "msg": "登录失效",
                    "data": {},
                },
            )

            with self.assertRaises(Exception) as raised:
                adapter.execute(
                    TaskRequest(
                        adapter_key="xhs",
                        capability="content_detail_by_url",
                        input=TaskInput(
                            url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"
                        ),
                    )
                )

        self.assertEqual(raised.exception.code, "xhs_detail_request_failed")
        self.assertIn("platform_code", raised.exception.details)
        self.assertEqual(raised.exception.details["platform_code"], 300013)
        self.assertEqual(raised.exception.details["platform_message"], "登录失效")

    def test_xhs_adapter_raises_platform_error_when_session_file_is_missing(self) -> None:
        adapter = XhsAdapter(session_path=Path("/tmp/syvert-does-not-exist/xhs.session.json"))

        with self.assertRaises(Exception) as raised:
            adapter.execute(
                TaskRequest(
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    input=TaskInput(url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"),
                )
            )
        self.assertEqual(raised.exception.code, "xhs_session_missing")

    def test_xhs_adapter_raises_sign_unavailable_when_sign_base_url_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "xhs.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                    }
                ),
                encoding="utf-8",
            )
            adapter = XhsAdapter(session_path=session_path)

            with self.assertRaises(Exception) as raised:
                adapter.execute(
                    TaskRequest(
                        adapter_key="xhs",
                        capability="content_detail_by_url",
                        input=TaskInput(
                            url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"
                        ),
                    )
                )
            self.assertEqual(raised.exception.code, "xhs_sign_unavailable")

    def test_xhs_adapter_raises_content_not_found_for_empty_detail_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "xhs.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = XhsAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {
                    "x_s": "signed-x-s",
                    "x_t": "signed-x-t",
                    "x_s_common": "signed-x-s-common",
                    "x_b3_traceid": "trace-1",
                },
                detail_transport=lambda **kwargs: {"items": []},
            )

            with self.assertRaises(Exception) as raised:
                adapter.execute(
                    TaskRequest(
                        adapter_key="xhs",
                        capability="content_detail_by_url",
                        input=TaskInput(
                            url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"
                        ),
                    )
                )
            self.assertEqual(raised.exception.code, "xhs_content_not_found")

    def test_xhs_adapter_normalizes_live_photo_as_mixed_media(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "xhs.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = XhsAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {
                    "x_s": "signed-x-s",
                    "x_t": "signed-x-t",
                    "x_s_common": "signed-x-s-common",
                    "x_b3_traceid": "trace-1",
                },
                detail_transport=lambda **kwargs: {
                    "items": [
                        {
                            "note_card": {
                                "note_id": "66fad51c000000001b0224b8",
                                "type": "normal",
                                "title": "Live Photo 标题",
                                "desc": "Live Photo 正文",
                                "time": 1712304300,
                                "user": {
                                    "user_id": "user-live-photo",
                                    "nickname": "作者乙",
                                    "avatar": "https://cdn.example/avatar-live.jpg",
                                },
                                "interact_info": {
                                    "liked_count": "1",
                                    "comment_count": "2",
                                    "share_count": "3",
                                    "collected_count": "4",
                                },
                                "image_list": [
                                    {
                                        "url_default": "https://cdn.example/live-photo-cover.jpg",
                                        "live_photo": True,
                                        "stream": {
                                            "h264": [
                                                {
                                                    "master_url": "https://cdn.example/live-photo.mp4",
                                                }
                                            ]
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            )

            payload = adapter.execute(
                TaskRequest(
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    input=TaskInput(
                        url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"
                    ),
                )
            )

        self.assertEqual(payload["normalized"]["content_type"], "mixed_media")
        self.assertEqual(payload["normalized"]["media"]["video_url"], "https://cdn.example/live-photo.mp4")
        self.assertEqual(
            payload["normalized"]["media"]["image_urls"],
            ["https://cdn.example/live-photo-cover.jpg"],
        )

    def test_xhs_adapter_coerces_invalid_numeric_fields_to_null(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_path = Path(temp_dir) / "xhs.session.json"
            session_path.write_text(
                json.dumps(
                    {
                        "cookies": "a=1; b=2",
                        "user_agent": "Mozilla/5.0 TestAgent",
                        "sign_base_url": "http://127.0.0.1:8000",
                    }
                ),
                encoding="utf-8",
            )
            adapter = XhsAdapter(
                session_path=session_path,
                sign_transport=lambda base_url, payload, timeout_seconds: {
                    "x_s": "signed-x-s",
                    "x_t": "signed-x-t",
                    "x_s_common": "signed-x-s-common",
                    "x_b3_traceid": "trace-1",
                },
                detail_transport=lambda **kwargs: {
                    "items": [
                        {
                            "note_card": {
                                "note_id": "66fad51c000000001b0224b8",
                                "type": "normal",
                                "title": "异常数值标题",
                                "desc": "异常数值正文",
                                "time": "999999999999999999999999999",
                                "user": {
                                    "user_id": "user-overflow",
                                    "nickname": "作者丙",
                                    "avatar": "https://cdn.example/avatar-overflow.jpg",
                                },
                                "interact_info": {
                                    "liked_count": "1e309",
                                    "comment_count": "2",
                                    "share_count": "3",
                                    "collected_count": "4",
                                },
                                "image_list": [
                                    {"url_default": "https://cdn.example/overflow-cover.jpg"}
                                ],
                            }
                        }
                    ]
                },
            )

            payload = adapter.execute(
                TaskRequest(
                    adapter_key="xhs",
                    capability="content_detail_by_url",
                    input=TaskInput(
                        url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"
                    ),
                )
            )

        self.assertEqual(payload["normalized"]["published_at"], None)
        self.assertEqual(payload["normalized"]["stats"]["like_count"], None)
        self.assertEqual(payload["normalized"]["stats"]["comment_count"], 2)

    def test_execute_task_returns_platform_failure_envelope_for_xhs_platform_errors(self) -> None:
        adapter = XhsAdapter(session_path=Path("/tmp/syvert-does-not-exist/xhs.session.json"))
        request = TaskRequest(
            adapter_key="xhs",
            capability="content_detail_by_url",
            input=TaskInput(url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"),
        )

        envelope = execute_task(
            request,
            adapters={"xhs": adapter},
            task_id_factory=lambda: "task-xhs-platform-error",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["task_id"], "task-xhs-platform-error")
        self.assertEqual(envelope["error"]["category"], "platform")
        self.assertEqual(envelope["error"]["code"], "xhs_session_missing")

    def test_runtime_rejects_incomplete_normalized_payload(self) -> None:
        class BrokenXhsAdapter:
            adapter_key = "xhs"
            supported_capabilities = frozenset({"content_detail_by_url"})

            def execute(self, request: TaskRequest) -> dict[str, Any]:
                return {
                    "raw": {"items": []},
                    "normalized": {
                        "platform": "xhs",
                        "content_id": "66fad51c000000001b0224b8",
                        "content_type": "image_post",
                        "canonical_url": request.input.url,
                        "title": "",
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

        envelope = execute_task(
            TaskRequest(
                adapter_key="xhs",
                capability="content_detail_by_url",
                input=TaskInput(url="https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"),
            ),
            adapters={"xhs": BrokenXhsAdapter()},
            task_id_factory=lambda: "task-xhs-invalid-success",
        )

        self.assertEqual(envelope["status"], "failed")
        self.assertEqual(envelope["error"]["category"], "runtime_contract")
        self.assertEqual(envelope["error"]["code"], "invalid_adapter_success_payload")

    def test_cli_module_path_can_load_xhs_adapter_and_execute_shared_core_path(self) -> None:
        handler_state: dict[str, Any] = {
            "sign_calls": [],
            "detail_calls": [],
        }

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                body = json.loads(raw_body or "{}")
                if self.path == "/signsrv/v1/xhs/sign":
                    handler_state["sign_calls"].append(
                        {
                            "headers": dict(self.headers),
                            "body": body,
                        }
                    )
                    response = {
                        "isok": True,
                        "data": {
                            "x_s": "signed-x-s",
                            "x_t": "signed-x-t",
                            "x_s_common": "signed-x-s-common",
                            "x_b3_traceid": "trace-1",
                        },
                    }
                elif self.path == "/api/sns/web/v1/feed":
                    handler_state["detail_calls"].append(
                        {
                            "headers": dict(self.headers),
                            "body": body,
                        }
                    )
                    response = {
                        "success": True,
                        "data": {
                            "items": [
                                {
                                    "note_card": {
                                        "note_id": "66fad51c000000001b0224b8",
                                        "type": "normal",
                                        "title": "CLI 标题",
                                        "desc": "CLI 正文",
                                        "time": 1712304300,
                                        "user": {
                                            "user_id": "cli-user-1",
                                            "nickname": "CLI 作者",
                                            "avatar": "https://cdn.example/avatar-cli.jpg",
                                        },
                                        "interact_info": {
                                            "liked_count": "21",
                                            "comment_count": "22",
                                            "share_count": "23",
                                            "collected_count": "24",
                                        },
                                        "image_list": [
                                            {"url_default": "https://cdn.example/cli-image-1.jpg"}
                                        ],
                                        "cover": {
                                            "url_default": "https://cdn.example/cli-cover.jpg"
                                        },
                                    }
                                }
                            ]
                        },
                    }
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp_home:
                session_path = Path(temp_home) / "xhs.session.json"
                session_path.write_text(
                    json.dumps(
                        {
                            "cookies": "a=1; b=2",
                            "user_agent": "Mozilla/5.0 TestAgent",
                            "sign_base_url": f"http://127.0.0.1:{server.server_port}",
                            "timeout_seconds": 5,
                        }
                    ),
                    encoding="utf-8",
                )
                stdout = io.StringIO()
                stderr = io.StringIO()
                with mock.patch("syvert.adapters.xhs.DEFAULT_XHS_SESSION_PATH", session_path), mock.patch(
                    "syvert.adapters.xhs.XHS_API_BASE_URL",
                    f"http://127.0.0.1:{server.server_port}",
                ):
                    exit_code = main(
                        [
                            "--adapter",
                            "xhs",
                            "--capability",
                            "content_detail_by_url",
                            "--url",
                            (
                                "https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8"
                                "?xsec_token=token-1&xsec_source=pc_search"
                            ),
                            "--adapter-module",
                            "syvert.adapters.xhs:build_adapters",
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
        self.assertEqual(payload["adapter_key"], "xhs")
        self.assertEqual(payload["capability"], "content_detail_by_url")
        self.assertEqual(payload["normalized"]["platform"], "xhs")
        self.assertEqual(payload["normalized"]["content_id"], "66fad51c000000001b0224b8")
        self.assertEqual(payload["normalized"]["content_type"], "image_post")
        self.assertEqual(payload["normalized"]["canonical_url"], "https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8")
        self.assertEqual(payload["normalized"]["media"]["image_urls"], ["https://cdn.example/cli-image-1.jpg"])
        self.assertEqual(payload["normalized"]["media"]["video_url"], None)
        self.assertEqual(len(handler_state["sign_calls"]), 1)
        self.assertEqual(len(handler_state["detail_calls"]), 1)
        self.assertEqual(handler_state["sign_calls"][0]["body"]["uri"], "/api/sns/web/v1/feed")
        self.assertEqual(
            handler_state["detail_calls"][0]["body"]["source_note_id"],
            "66fad51c000000001b0224b8",
        )
        self.assertEqual(
            handler_state["detail_calls"][0]["body"]["xsec_token"],
            "token-1",
        )
