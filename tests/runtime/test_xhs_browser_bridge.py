from __future__ import annotations

import json
import subprocess
import unittest


class XhsBrowserBridgeTests(unittest.TestCase):
    def test_parse_chrome_tab_listing_parses_newline_delimited_rows(self) -> None:
        from syvert.adapters.xhs_browser_bridge import parse_chrome_tab_listing

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

    def test_parse_chrome_tab_listing_preserves_url_when_title_contains_pipe(self) -> None:
        from syvert.adapters.xhs_browser_bridge import parse_chrome_tab_listing

        tabs = parse_chrome_tab_listing(
            "101|标题A | 标题B|https://www.xiaohongshu.com/explore/abcd1234?xsec_token=token"
        )

        self.assertEqual(len(tabs), 1)
        self.assertEqual(tabs[0].title, "标题A | 标题B")
        self.assertEqual(
            tabs[0].url,
            "https://www.xiaohongshu.com/explore/abcd1234?xsec_token=token",
        )

    def test_select_xhs_tab_requires_exact_target_url(self) -> None:
        from syvert.adapters.xhs_browser_bridge import ChromeTab, select_xhs_tab
        from syvert.runtime import PlatformAdapterError

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

    def test_select_xhs_tab_accepts_same_note_id_when_query_differs(self) -> None:
        from syvert.adapters.xhs_browser_bridge import ChromeTab, select_xhs_tab

        tab = select_xhs_tab(
            [
                ChromeTab(
                    tab_id="1",
                    title="小红书详情",
                    url="https://www.xiaohongshu.com/explore/abcd1234",
                )
            ],
            target_url="https://www.xiaohongshu.com/explore/abcd1234?xsec_token=token&xsec_source=",
        )

        self.assertEqual(tab.tab_id, "1")

    def test_select_xhs_tab_accepts_canonical_url_for_same_note_id(self) -> None:
        from syvert.adapters.xhs_browser_bridge import ChromeTab, select_xhs_tab

        tab = select_xhs_tab(
            [
                ChromeTab(
                    tab_id="1",
                    title="目标详情页",
                    url="https://www.xiaohongshu.com/explore/abcd1234",
                )
            ],
            target_url="https://www.xiaohongshu.com/explore/abcd1234?xsec_token=token&xsec_source=",
        )

        self.assertEqual(tab.tab_id, "1")

    def test_extract_page_state_rejects_invalid_json(self) -> None:
        from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge
        from syvert.runtime import PlatformAdapterError

        outputs = iter(
            [
                "1|目标页|https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
                "{not-json",
            ]
        )
        bridge = XhsAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.extract_page_state(
                target_url="https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
                source_note_id="abcd",
            )

        self.assertEqual(raised.exception.code, "xhs_browser_payload_invalid")

    def test_extract_page_state_rejects_note_id_mismatch(self) -> None:
        from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge
        from syvert.runtime import PlatformAdapterError

        outputs = iter(
            [
                "1|目标页|https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
                '{"note":{"currentNoteId":"other-note","noteDetailMap":{"other-note":{"note":{"noteId":"other-note"}}}}}',
            ]
        )
        bridge = XhsAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.extract_page_state(
                target_url="https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
                source_note_id="abcd",
            )

        self.assertEqual(raised.exception.code, "xhs_browser_note_mismatch")

    def test_extract_page_state_preserves_original_page_state_shape(self) -> None:
        from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge

        raw_state = {
            "note": {
                "currentNoteId": "abcd",
                "noteDetailMap": {
                    "abcd": {
                        "note": {
                            "noteId": "abcd",
                            "title": "目标标题",
                        }
                    }
                },
            },
            "extra": {
                "trace": "keep-me",
            },
        }
        outputs = iter(
            [
                "1|目标页|https://www.xiaohongshu.com/explore/abcd",
                '{"note":{"currentNoteId":"abcd","noteDetailMap":{"abcd":{"note":{"noteId":"abcd","title":"目标标题"}}}},"extra":{"trace":"keep-me"}}',
            ]
        )
        bridge = XhsAuthenticatedBrowserBridge(run_applescript=lambda script: next(outputs))

        state = bridge.extract_page_state(
            target_url="https://www.xiaohongshu.com/explore/abcd?xsec_token=token",
            source_note_id="abcd",
        )

        self.assertEqual(state, raw_state)

    def test_list_tabs_maps_javascript_disabled_error(self) -> None:
        from syvert.adapters.xhs_browser_bridge import (
            CHROME_JS_DISABLED_SNIPPET,
            XhsAuthenticatedBrowserBridge,
        )
        from syvert.runtime import PlatformAdapterError

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
        from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge
        from syvert.runtime import PlatformAdapterError

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

    def test_list_tabs_maps_oserror_to_platform_error(self) -> None:
        from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge
        from syvert.runtime import PlatformAdapterError

        def raise_error(script: str) -> str:
            raise FileNotFoundError("osascript missing")

        bridge = XhsAuthenticatedBrowserBridge(run_applescript=raise_error)

        with self.assertRaises(PlatformAdapterError) as raised:
            bridge.list_tabs()

        self.assertEqual(raised.exception.code, "xhs_browser_command_failed")

    def test_build_in_page_javascript_extracts_note_from_inline_state(self) -> None:
        from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge

        bridge = XhsAuthenticatedBrowserBridge()
        inline_state = (
            'window.__INITIAL_STATE__={"note":{"noteDetailMap":{"abcd1234":{"note":{"noteId":"abcd1234","title":"页面标题"}}}}}'
        )
        script = bridge._build_in_page_javascript(source_note_id="abcd1234")
        node_script = f"""
global.window = {{}};
global.document = {{
  scripts: [{{textContent: {json.dumps(inline_state)}}}]
}};
const result = {script};
process.stdout.write(result);
"""

        completed = subprocess.run(
            ["node", "-e", node_script],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["note"]["noteDetailMap"]["abcd1234"]["note"]["noteId"], "abcd1234")
        self.assertEqual(payload["note"]["noteDetailMap"]["abcd1234"]["note"]["title"], "页面标题")

    def test_build_in_page_javascript_accepts_inline_state_trailing_semicolon(self) -> None:
        from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge

        bridge = XhsAuthenticatedBrowserBridge()
        inline_state = (
            'window.__INITIAL_STATE__={"note":{"noteDetailMap":{"abcd1234":{"note":{"noteId":"abcd1234","title":"页面标题"}}}}};'
        )
        script = bridge._build_in_page_javascript(source_note_id="abcd1234")
        node_script = f"""
global.window = {{}};
global.document = {{
  scripts: [{{textContent: {json.dumps(inline_state)}}}]
}};
const result = {script};
process.stdout.write(result);
"""

        completed = subprocess.run(
            ["node", "-e", node_script],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["note"]["noteDetailMap"]["abcd1234"]["note"]["noteId"], "abcd1234")

    def test_build_in_page_javascript_preserves_literal_undefined_text(self) -> None:
        from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge

        bridge = XhsAuthenticatedBrowserBridge()
        inline_state = (
            'window.__INITIAL_STATE__={"note":{"noteDetailMap":{"abcd1234":{"note":{"noteId":"abcd1234","title":"undefined 提示文本"}}}},"extra":{"marker":undefined}};'
        )
        script = bridge._build_in_page_javascript(source_note_id="abcd1234")
        node_script = f"""
global.window = {{}};
global.document = {{
  scripts: [{{textContent: {json.dumps(inline_state)}}}]
}};
const result = {script};
process.stdout.write(result);
"""

        completed = subprocess.run(
            ["node", "-e", node_script],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["note"]["noteDetailMap"]["abcd1234"]["note"]["title"],
            "undefined 提示文本",
        )
