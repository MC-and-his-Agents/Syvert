from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess

from syvert.runtime import PlatformAdapterError


CHROME_JS_DISABLED_SNIPPET = "通过 AppleScript 执行 JavaScript 的功能已关闭"


@dataclass(frozen=True)
class ChromeTab:
    tab_id: str
    title: str
    url: str


def parse_chrome_tab_listing(text: str) -> list[ChromeTab]:
    tabs: list[ChromeTab] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        tab_id, title, url = parts
        tabs.append(ChromeTab(tab_id=tab_id, title=title, url=url))
    return tabs


def select_xhs_tab(tabs: list[ChromeTab], *, target_url: str) -> ChromeTab:
    for tab in tabs:
        if tab.url == target_url:
            return tab
    for tab in tabs:
        if is_xhs_url(tab.url):
            return tab
    raise PlatformAdapterError(
        code="xhs_browser_tab_missing",
        message="未找到已打开的小红书浏览器标签页",
    )


def is_xhs_url(url: str) -> bool:
    return "xiaohongshu.com" in url


def default_run_applescript(script: str) -> str:
    completed = subprocess.run(
        ["osascript"],
        input=script,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout


class XhsAuthenticatedBrowserBridge:
    def __init__(self, *, run_applescript=default_run_applescript) -> None:
        self._run_applescript = run_applescript

    def list_tabs(self) -> list[ChromeTab]:
        output = self._run_script(self._build_list_tabs_script())
        return parse_chrome_tab_listing(output)

    def extract_note_payload(self, *, target_url: str, source_note_id: str) -> dict[str, object]:
        tab = select_xhs_tab(self.list_tabs(), target_url=target_url)
        script = self._build_extract_note_script(tab=tab, source_note_id=source_note_id)
        raw_payload = self._run_script(script).strip()
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as error:
            raise PlatformAdapterError(
                code="xhs_browser_payload_invalid",
                message="浏览器桥接返回的内容不是合法 JSON",
                details={"error": str(error)},
            ) from error
        if not isinstance(payload, dict):
            raise PlatformAdapterError(
                code="xhs_browser_payload_invalid",
                message="浏览器桥接返回的 note payload 形状不合法",
            )
        note_id = payload.get("note_id")
        if not isinstance(note_id, str) or not note_id:
            note_id = payload.get("noteId")
        if isinstance(note_id, str) and note_id and note_id != source_note_id:
            raise PlatformAdapterError(
                code="xhs_browser_note_mismatch",
                message="浏览器标签页返回的 note_id 与目标不一致",
                details={"expected_note_id": source_note_id, "actual_note_id": note_id},
            )
        return payload

    def _run_script(self, script: str) -> str:
        try:
            return self._run_applescript(script)
        except subprocess.CalledProcessError as error:
            stderr = error.stderr or ""
            if CHROME_JS_DISABLED_SNIPPET in stderr:
                raise PlatformAdapterError(
                    code="xhs_browser_javascript_disabled",
                    message="Chrome 未启用 AppleScript JavaScript 执行能力",
                ) from error
            raise PlatformAdapterError(
                code="xhs_browser_command_failed",
                message="执行浏览器桥接脚本失败",
                details={"stderr": stderr, "returncode": error.returncode},
            ) from error

    def _build_list_tabs_script(self) -> str:
        return """
tell application "Google Chrome"
    set outputLines to {}
    repeat with eachWindow in windows
        repeat with eachTab in tabs of eachWindow
            set end of outputLines to ((id of eachTab as text) & "|" & (title of eachTab as text) & "|" & (URL of eachTab as text))
        end repeat
    end repeat
    set previousDelimiters to AppleScript's text item delimiters
    set AppleScript's text item delimiters to linefeed
    set outputText to outputLines as text
    set AppleScript's text item delimiters to previousDelimiters
    return outputText
end tell
""".strip()

    def _build_extract_note_script(self, *, tab: ChromeTab, source_note_id: str) -> str:
        js = json.dumps(self._build_in_page_javascript(source_note_id=source_note_id))
        return f"""
tell application "Google Chrome"
    repeat with eachWindow in windows
        repeat with eachTab in tabs of eachWindow
            if (id of eachTab as text) is "{tab.tab_id}" then
                return execute eachTab javascript {js}
            end if
        end repeat
    end repeat
end tell
""".strip()

    def _build_in_page_javascript(self, *, source_note_id: str) -> str:
        serialized_note_id = json.dumps(source_note_id)
        return f"""
(function() {{
  const sourceNoteId = {serialized_note_id};
  const inlineStateScript = Array.from(document.scripts)
    .map((script) => script.textContent || "")
    .find((text) => text.includes("window.__INITIAL_STATE__=")) || "";
  const rawState = inlineStateScript.startsWith("window.__INITIAL_STATE__=")
    ? inlineStateScript.slice("window.__INITIAL_STATE__=".length)
    : "";
  const root = window.__INITIAL_STATE__ || (rawState ? Function('return (' + rawState + ');')() : null);
  const noteRoot = root && root.note;
  const detailMap = noteRoot && noteRoot.noteDetailMap;
  const candidate =
    (detailMap && detailMap[sourceNoteId] && detailMap[sourceNoteId].note) ||
    (detailMap && Object.values(detailMap).find(Boolean) && Object.values(detailMap).find(Boolean).note) ||
    null;
  if (!candidate) {{
    throw new Error("xhs note payload missing");
  }}
  return JSON.stringify(candidate);
}})();
""".strip()
