from __future__ import annotations

import json
import subprocess
import unittest
from urllib import parse


class DouyinBrowserBridgeTests(unittest.TestCase):
    def test_parse_chrome_tab_listing_parses_newline_delimited_rows(self) -> None:
        from syvert.adapters.douyin_browser_bridge import parse_chrome_tab_listing

        tabs = parse_chrome_tab_listing(
            "\n".join(
                [
                    "101|ChatGPT|https://chatgpt.com/",
                    "102|抖音详情|https://www.douyin.com/video/7580570616932224282",
                ]
            )
        )

        self.assertEqual(len(tabs), 2)
        self.assertEqual(tabs[0].tab_id, "101")
        self.assertEqual(tabs[1].url, "https://www.douyin.com/video/7580570616932224282")

    def test_select_douyin_tab_accepts_share_url_for_same_aweme_id(self) -> None:
        from syvert.adapters.douyin_browser_bridge import ChromeTab, select_douyin_tab

        tab = select_douyin_tab(
            [
                ChromeTab(
                    tab_id="1",
                    title="抖音详情",
                    url="https://www.douyin.com/video/7580570616932224282",
                )
            ],
            target_url=(
                "https://www.iesdouyin.com/share/video/7580570616932224282/"
                "?region=CN&mid=mid-1"
            ),
        )

        self.assertEqual(tab.tab_id, "1")

    def test_select_douyin_tab_rejects_non_detail_tab(self) -> None:
        from syvert.adapters.douyin_browser_bridge import ChromeTab, select_douyin_tab
        from syvert.runtime import PlatformAdapterError

        with self.assertRaises(PlatformAdapterError) as raised:
            select_douyin_tab(
                [
                    ChromeTab(
                        tab_id="1",
                        title="抖音首页",
                        url="https://www.douyin.com/discover",
                    )
                ],
                target_url="https://www.douyin.com/video/7580570616932224282",
            )

        self.assertEqual(raised.exception.code, "douyin_browser_target_tab_missing")

    def test_extract_aweme_detail_from_page_state_prefers_ssr_then_render_then_sigi(self) -> None:
        from syvert.adapters.douyin_browser_bridge import extract_aweme_detail_from_page_state

        payload = extract_aweme_detail_from_page_state(
            {
                "SSR_RENDER_DATA": {
                    "aweme_detail": {
                        "aweme_id": "7580570616932224282",
                        "desc": "SSR 命中",
                    }
                },
                "RENDER_DATA": {
                    "aweme_detail": {
                        "aweme_id": "7580570616932224282",
                        "desc": "RENDER 命中",
                    }
                },
                "SIGI_STATE": {
                    "ItemModule": {
                        "7580570616932224282": {
                            "aweme_id": "7580570616932224282",
                            "desc": "SIGI 命中",
                        }
                    }
                },
            },
            source_aweme_id="7580570616932224282",
        )

        self.assertEqual(payload["aweme_id"], "7580570616932224282")
        self.assertEqual(payload["desc"], "SSR 命中")

    def test_extract_aweme_detail_from_page_state_falls_back_to_sigi_item_module(self) -> None:
        from syvert.adapters.douyin_browser_bridge import extract_aweme_detail_from_page_state

        payload = extract_aweme_detail_from_page_state(
            {
                "SSR_RENDER_DATA": {"aweme_detail": {"aweme_id": "other"}},
                "RENDER_DATA": {},
                "SIGI_STATE": {
                    "ItemModule": {
                        "7580570616932224282": {
                            "aweme_id": "7580570616932224282",
                            "desc": "SIGI 命中",
                        }
                    }
                },
            },
            source_aweme_id="7580570616932224282",
        )

        self.assertEqual(payload["desc"], "SIGI 命中")

    def test_extract_aweme_detail_from_page_state_decodes_percent_encoded_render_data_string(self) -> None:
        from syvert.adapters.douyin_browser_bridge import extract_aweme_detail_from_page_state

        encoded_render_data = parse.quote(
            json.dumps(
                {
                    "aweme_detail": {
                        "aweme_id": "7580570616932224282",
                        "desc": "RENDER string 命中",
                    }
                },
                ensure_ascii=False,
            )
        )

        payload = extract_aweme_detail_from_page_state(
            {"RENDER_DATA": encoded_render_data},
            source_aweme_id="7580570616932224282",
        )

        self.assertEqual(payload["desc"], "RENDER string 命中")

    def test_extract_aweme_detail_from_page_state_rejects_missing_target(self) -> None:
        from syvert.adapters.douyin_browser_bridge import extract_aweme_detail_from_page_state
        from syvert.runtime import PlatformAdapterError

        with self.assertRaises(PlatformAdapterError) as raised:
            extract_aweme_detail_from_page_state(
                {
                    "SSR_RENDER_DATA": {"aweme_detail": {"aweme_id": "other"}},
                    "RENDER_DATA": {},
                    "SIGI_STATE": {},
                },
                source_aweme_id="7580570616932224282",
            )

        self.assertEqual(raised.exception.code, "douyin_content_not_found")

    def test_extract_aweme_detail_from_page_state_accepts_browser_detail_recovery_payload(self) -> None:
        from syvert.adapters.douyin_browser_bridge import extract_aweme_detail_from_page_state

        payload = extract_aweme_detail_from_page_state(
            {
                "SSR_RENDER_DATA": {},
                "RENDER_DATA": {},
                "SIGI_STATE": {},
                "AWEME_DETAIL": {
                    "aweme_id": "7580570616932224282",
                    "desc": "浏览器请求命中",
                },
            },
            source_aweme_id="7580570616932224282",
        )

        self.assertEqual(payload["desc"], "浏览器请求命中")

    def test_extract_page_state_rejects_invalid_json(self) -> None:
        from syvert.adapters.douyin_browser_bridge import DouyinAuthenticatedBrowserBridge
        from syvert.runtime import PlatformAdapterError

        outputs = iter(
            [
                "1|目标页|https://www.douyin.com/video/7580570616932224282",
                "{not-json",
            ]
        )
        bridge = DouyinAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.extract_page_state(
                target_url="https://www.douyin.com/video/7580570616932224282",
                source_aweme_id="7580570616932224282",
            )

        self.assertEqual(raised.exception.code, "douyin_browser_payload_invalid")

    def test_extract_page_state_rejects_missing_target_aweme(self) -> None:
        from syvert.adapters.douyin_browser_bridge import DouyinAuthenticatedBrowserBridge
        from syvert.runtime import PlatformAdapterError

        outputs = iter(
            [
                "1|目标页|https://www.douyin.com/video/7580570616932224282",
                json.dumps(
                    {
                        "SSR_RENDER_DATA": {
                            "aweme_detail": {
                                "aweme_id": "other-aweme",
                            }
                        }
                    }
                ),
            ]
        )
        bridge = DouyinAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.extract_page_state(
                target_url="https://www.douyin.com/video/7580570616932224282",
                source_aweme_id="7580570616932224282",
            )

        self.assertEqual(raised.exception.code, "douyin_content_not_found")

    def test_extract_page_state_preserves_original_page_state_shape(self) -> None:
        from syvert.adapters.douyin_browser_bridge import DouyinAuthenticatedBrowserBridge

        raw_state = {
            "SSR_RENDER_DATA": {
                "aweme_detail": {
                    "aweme_id": "7580570616932224282",
                    "desc": "页面态标题",
                }
            },
            "meta": {"trace": "keep-me"},
        }
        outputs = iter(
            [
                "1|目标页|https://www.douyin.com/video/7580570616932224282",
                json.dumps(raw_state, ensure_ascii=False),
            ]
        )
        bridge = DouyinAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        payload = bridge.extract_page_state(
            target_url="https://www.douyin.com/video/7580570616932224282",
            source_aweme_id="7580570616932224282",
        )

        self.assertEqual(payload, raw_state)

    def test_extract_page_state_falls_back_to_authenticated_detail_request_when_page_state_misses_target(self) -> None:
        from syvert.adapters.douyin_browser_bridge import DouyinAuthenticatedBrowserBridge

        def run_applescript(script: str) -> str:
            if "set outputLines" in script:
                return "1|目标页|https://www.douyin.com/video/7580570616932224282"
            if 'const normalizeRoot = (value) => {' in script:
                return json.dumps({"SSR_RENDER_DATA": {}, "RENDER_DATA": {}, "SIGI_STATE": {}})
            if "localStorage.getItem('__tea_cache_tokens_6383')" in script:
                return json.dumps(
                    {
                        "userAgent": "Mozilla/5.0 TestAgent",
                        "verifyFp": "verify-browser-1",
                        "webid": "webid-browser-1",
                        "xmst": "ms-token-browser-1",
                        "cookies": "s_v_web_id=verify-browser-1",
                    }
                )
            if "new XMLHttpRequest()" in script:
                return json.dumps(
                    {
                        "status": 200,
                        "text": json.dumps(
                            {
                                "aweme_detail": {
                                    "aweme_id": "7580570616932224282",
                                    "desc": "浏览器请求命中",
                                }
                            },
                            ensure_ascii=False,
                        ),
                    }
                )
            raise AssertionError(script)

        bridge = DouyinAuthenticatedBrowserBridge(run_applescript=run_applescript)

        payload = bridge.extract_page_state(
            target_url="https://www.douyin.com/video/7580570616932224282",
            source_aweme_id="7580570616932224282",
            sign_base_url="http://127.0.0.1:8989",
        )

        self.assertEqual(payload["AWEME_DETAIL"]["desc"], "浏览器请求命中")

    def test_extract_page_state_accepts_percent_encoded_render_data_payload(self) -> None:
        from syvert.adapters.douyin_browser_bridge import DouyinAuthenticatedBrowserBridge

        raw_state = {
            "RENDER_DATA": parse.quote(
                json.dumps(
                    {
                        "aweme_detail": {
                            "aweme_id": "7580570616932224282",
                            "desc": "脚本节点解码成功",
                        }
                    },
                    ensure_ascii=False,
                )
            )
        }
        outputs = iter(
            [
                "1|目标页|https://www.douyin.com/video/7580570616932224282",
                json.dumps(raw_state, ensure_ascii=False),
            ]
        )
        bridge = DouyinAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        payload = bridge.extract_page_state(
            target_url="https://www.douyin.com/video/7580570616932224282",
            source_aweme_id="7580570616932224282",
        )

        self.assertEqual(payload, raw_state)

    def test_list_tabs_maps_javascript_disabled_error(self) -> None:
        from syvert.adapters.douyin_browser_bridge import (
            CHROME_JS_DISABLED_SNIPPET,
            DouyinAuthenticatedBrowserBridge,
        )
        from syvert.runtime import PlatformAdapterError

        def raise_error(script: str) -> str:
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["osascript"],
                stderr=CHROME_JS_DISABLED_SNIPPET,
            )

        bridge = DouyinAuthenticatedBrowserBridge(run_applescript=raise_error)

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.list_tabs()

        self.assertEqual(raised.exception.code, "douyin_browser_javascript_disabled")
