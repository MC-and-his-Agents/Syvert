from __future__ import annotations

import subprocess
import unittest


class XhsBrowserBridgeTests(unittest.TestCase):
    def test_parse_chrome_tab_listing_parses_newline_delimited_rows(self) -> None:
        from syvert.xhs_browser_bridge import parse_chrome_tab_listing

        tabs = parse_chrome_tab_listing(
            "\n".join(
                [
                    "101|ChatGPT|https://chatgpt.com/",
                    "102|小红书 - 你的生活兴趣社区|https://www.xiaohongshu.com/explore",
                ]
            )
        )

        self.assertEqual(len(tabs), 2)
        self.assertEqual(tabs[0].tab_id, "101")
        self.assertEqual(tabs[1].url, "https://www.xiaohongshu.com/explore")

    def test_select_xhs_tab_requires_exact_target_url(self) -> None:
        from syvert.runtime import PlatformAdapterError
        from syvert.xhs_browser_bridge import ChromeTab, select_xhs_tab

        with self.assertRaises(PlatformAdapterError) as raised:
            select_xhs_tab(
                [
                    ChromeTab(
                        tab_id="1",
                        title="小红书首页",
                        url="https://www.xiaohongshu.com/explore",
                    )
                ],
                target_url="https://www.xiaohongshu.com/explore/abcd1234?xsec_token=token",
            )

        self.assertEqual(raised.exception.code, "xhs_browser_target_tab_missing")

    def test_extract_note_payload_rejects_invalid_json(self) -> None:
        from syvert.runtime import PlatformAdapterError
        from syvert.xhs_browser_bridge import XhsAuthenticatedBrowserBridge

        outputs = iter(
            [
                "1|目标页|https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
                "{not-json",
            ]
        )
        bridge = XhsAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.extract_note_payload(
                target_url="https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
                source_note_id="abcd",
            )

        self.assertEqual(raised.exception.code, "xhs_browser_payload_invalid")

    def test_extract_note_payload_rejects_note_id_mismatch(self) -> None:
        from syvert.runtime import PlatformAdapterError
        from syvert.xhs_browser_bridge import XhsAuthenticatedBrowserBridge

        outputs = iter(
            [
                "1|目标页|https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
                '{"noteId":"other-note","title":"错误页"}',
            ]
        )
        bridge = XhsAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.extract_note_payload(
                target_url="https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
                source_note_id="abcd",
            )

        self.assertEqual(raised.exception.code, "xhs_browser_note_mismatch")

    def test_list_tabs_maps_javascript_disabled_error(self) -> None:
        from syvert.runtime import PlatformAdapterError
        from syvert.xhs_browser_bridge import (
            CHROME_JS_DISABLED_SNIPPET,
            XhsAuthenticatedBrowserBridge,
        )

        def raise_error(script: str) -> str:
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["osascript"],
                stderr=CHROME_JS_DISABLED_SNIPPET,
            )

        bridge = XhsAuthenticatedBrowserBridge(run_applescript=raise_error)

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.list_tabs()

        self.assertEqual(raised.exception.code, "xhs_browser_javascript_disabled")

    def test_list_tabs_maps_generic_command_failure(self) -> None:
        from syvert.runtime import PlatformAdapterError
        from syvert.xhs_browser_bridge import XhsAuthenticatedBrowserBridge

        def raise_error(script: str) -> str:
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["osascript"],
                stderr="AppleEvent timed out",
            )

        bridge = XhsAuthenticatedBrowserBridge(run_applescript=raise_error)

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.list_tabs()

        self.assertEqual(raised.exception.code, "xhs_browser_command_failed")
