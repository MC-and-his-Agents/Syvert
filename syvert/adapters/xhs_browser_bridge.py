from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from urllib import parse

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
        try:
            tab_id, remainder = line.split("|", 1)
            title, url = remainder.rsplit("|", 1)
        except ValueError:
            continue
        tabs.append(ChromeTab(tab_id=tab_id, title=title, url=url))
    return tabs


def select_xhs_tab(tabs: list[ChromeTab], *, target_url: str) -> ChromeTab:
    target_note_id = extract_xhs_note_id_from_url(target_url)
    target_path = canonicalize_xhs_url_path(target_url)
    for tab in tabs:
        if tab.url == target_url:
            return tab
    for tab in tabs:
        if not is_xhs_url(tab.url):
            continue
        if target_note_id and extract_xhs_note_id_from_url(tab.url) == target_note_id:
            return tab
    for tab in tabs:
        if not is_xhs_url(tab.url):
            continue
        if target_path and canonicalize_xhs_url_path(tab.url) == target_path:
            return tab
    raise PlatformAdapterError(
        code="xhs_browser_target_tab_missing",
        message="未找到目标小红书详情标签页",
        details={"target_url": target_url},
    )


def is_xhs_url(url: str) -> bool:
    return "xiaohongshu.com" in url


def extract_xhs_note_id_from_url(url: str) -> str:
    try:
        parsed = parse.urlparse(url)
    except ValueError:
        return ""
    if parsed.netloc not in {"www.xiaohongshu.com", "xiaohongshu.com"}:
        return ""
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] in {"explore", "discovery"}:
        return parts[-1]
    return ""


def canonicalize_xhs_url_path(url: str) -> str:
    try:
        parsed = parse.urlparse(url)
    except ValueError:
        return ""
    if parsed.netloc not in {"www.xiaohongshu.com", "xiaohongshu.com"}:
        return ""
    return parsed.path.rstrip("/")


def default_run_applescript(script: str, *, timeout_seconds: int) -> str:
    completed = subprocess.run(
        ["osascript"],
        input=script,
        text=True,
        capture_output=True,
        check=True,
        timeout=max(timeout_seconds, 1),
    )
    return completed.stdout


class XhsAuthenticatedBrowserBridge:
    def __init__(self, *, run_applescript=default_run_applescript, timeout_seconds: int = 10) -> None:
        self._run_applescript = run_applescript
        self._timeout_seconds = max(timeout_seconds, 1)

    def list_tabs(self) -> list[ChromeTab]:
        output = self._run_script(self._build_list_tabs_script())
        return parse_chrome_tab_listing(output)

    def extract_page_state(self, *, target_url: str, source_note_id: str) -> dict[str, object]:
        tab = select_xhs_tab(self.list_tabs(), target_url=target_url)
        script = self._build_extract_page_state_script(tab=tab, source_note_id=source_note_id)
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
                message="浏览器桥接返回的页面态形状不合法",
            )
        self._ensure_page_state_matches_target(payload, source_note_id=source_note_id)
        return payload

    def _run_script(self, script: str) -> str:
        try:
            return self._invoke_run_applescript(script)
        except subprocess.TimeoutExpired as error:
            raise PlatformAdapterError(
                code="xhs_browser_command_failed",
                message="执行浏览器桥接脚本失败",
                details={"timeout_seconds": self._timeout_seconds, "error_type": error.__class__.__name__},
            ) from error
        except subprocess.CalledProcessError as error:
            stderr = error.stderr or ""
            if is_javascript_disabled_error(stderr):
                raise PlatformAdapterError(
                    code="xhs_browser_javascript_disabled",
                    message="Chrome 未启用 AppleScript JavaScript 执行能力",
                ) from error
            raise PlatformAdapterError(
                code="xhs_browser_command_failed",
                message="执行浏览器桥接脚本失败",
                details={"stderr": stderr, "returncode": error.returncode},
            ) from error
        except OSError as error:
            raise PlatformAdapterError(
                code="xhs_browser_command_failed",
                message="执行浏览器桥接脚本失败",
                details={"error_type": error.__class__.__name__},
            ) from error

    def _invoke_run_applescript(self, script: str) -> str:
        try:
            return self._run_applescript(script, timeout_seconds=self._timeout_seconds)
        except TypeError as error:
            if "timeout_seconds" not in str(error):
                raise
            return self._run_applescript(script)

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

    def _build_extract_page_state_script(self, *, tab: ChromeTab, source_note_id: str) -> str:
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
  const sanitizeInlineState = (rawState) => {{
    if (!rawState) {{
      return "";
    }}
    let sanitized = rawState.trim();
    if (sanitized.endsWith(";")) {{
      sanitized = sanitized.slice(0, -1).trimEnd();
    }}
    return sanitized;
  }};
  const inlineStateScript = Array.from(document.scripts)
    .map((script) => script.textContent || "")
    .find((text) => text.includes("window.__INITIAL_STATE__=")) || "";
  const rawState = inlineStateScript.startsWith("window.__INITIAL_STATE__=")
    ? inlineStateScript.slice("window.__INITIAL_STATE__=".length)
    : "";
  const sanitizedState = sanitizeInlineState(rawState);
  const root = window.__INITIAL_STATE__ || (sanitizedState ? Function('return (' + sanitizedState + ');')() : null);
  const noteRoot = root && root.note;
  const detailMap = noteRoot && noteRoot.noteDetailMap;
  const candidate =
    (detailMap && detailMap[sourceNoteId] && detailMap[sourceNoteId].note) ||
    (detailMap && Object.values(detailMap).find(Boolean) && Object.values(detailMap).find(Boolean).note) ||
    null;
  if (!candidate) {{
    throw new Error("xhs note payload missing");
  }}
  return JSON.stringify(root);
}})();
""".strip()

    def _ensure_page_state_matches_target(self, payload: dict[str, object], *, source_note_id: str) -> None:
        note_root = payload.get("note")
        if not isinstance(note_root, dict):
            raise PlatformAdapterError(
                code="xhs_browser_payload_invalid",
                message="浏览器桥接返回的页面态缺少 note",
            )
        detail_map = note_root.get("noteDetailMap")
        if not isinstance(detail_map, dict):
            raise PlatformAdapterError(
                code="xhs_browser_payload_invalid",
                message="浏览器桥接返回的页面态缺少 noteDetailMap",
            )
        target_entry = detail_map.get(source_note_id)
        if not isinstance(target_entry, dict):
            raise PlatformAdapterError(
                code="xhs_browser_note_mismatch",
                message="浏览器标签页返回的 note_id 与目标不一致",
                details={"expected_note_id": source_note_id},
            )
        note = target_entry.get("note")
        if not isinstance(note, dict):
            raise PlatformAdapterError(
                code="xhs_browser_payload_invalid",
                message="浏览器桥接返回的页面态缺少 note",
            )
        note_id = note.get("note_id")
        if not isinstance(note_id, str) or not note_id:
            note_id = note.get("noteId")
        if not isinstance(note_id, str) or not note_id:
            raise PlatformAdapterError(
                code="xhs_browser_payload_invalid",
                message="浏览器桥接返回的页面态缺少真实 note_id",
            )
        if note_id != source_note_id:
            raise PlatformAdapterError(
                code="xhs_browser_note_mismatch",
                message="浏览器标签页返回的 note_id 与目标不一致",
                details={"expected_note_id": source_note_id, "actual_note_id": note_id},
            )


def is_javascript_disabled_error(stderr: str) -> bool:
    if CHROME_JS_DISABLED_SNIPPET in stderr:
        return True
    lowered = stderr.casefold()
    if "javascript" not in lowered or "disable" not in lowered:
        return False
    return any(token in lowered for token in ("apple event", "apple events", "applescript"))
