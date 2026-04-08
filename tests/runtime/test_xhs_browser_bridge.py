from __future__ import annotations

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
