from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from urllib import error, parse, request

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


def select_douyin_tab(tabs: list[ChromeTab], *, target_url: str) -> ChromeTab:
    target_aweme_id = extract_douyin_aweme_id_from_url(target_url)
    for tab in tabs:
        if tab.url == target_url:
            return tab
    for tab in tabs:
        if target_aweme_id and extract_douyin_aweme_id_from_url(tab.url) == target_aweme_id:
            return tab
    raise PlatformAdapterError(
        code="douyin_browser_target_tab_missing",
        message="未找到目标抖音详情标签页",
        details={"target_url": target_url},
    )


def extract_douyin_aweme_id_from_url(url: str) -> str:
    try:
        parsed = parse.urlparse(url)
    except ValueError:
        return ""
    host = parsed.netloc.lower()
    parts = [part for part in parsed.path.split("/") if part]
    if host in {"www.douyin.com", "douyin.com"} and len(parts) == 2 and parts[0] == "video":
        return parts[1] if parts[1].isdigit() else ""
    if host in {"www.iesdouyin.com", "iesdouyin.com"} and len(parts) >= 3 and parts[0] == "share" and parts[1] == "video":
        return parts[2] if parts[2].isdigit() else ""
    return ""


def extract_aweme_detail_from_page_state(
    payload: dict[str, object],
    *,
    source_aweme_id: str,
) -> dict[str, object]:
    aweme_detail = (
        pick_aweme_detail(payload.get("SSR_RENDER_DATA"), source_aweme_id=source_aweme_id)
        or pick_aweme_detail(payload.get("RENDER_DATA"), source_aweme_id=source_aweme_id)
        or pick_aweme_detail(payload.get("SIGI_STATE"), source_aweme_id=source_aweme_id)
        or pick_aweme_detail(payload.get("AWEME_DETAIL"), source_aweme_id=source_aweme_id)
    )
    if aweme_detail is None:
        raise PlatformAdapterError(
            code="douyin_content_not_found",
            message="抖音页面态缺少目标 aweme",
            details={"source_aweme_id": source_aweme_id},
        )
    return aweme_detail


def pick_aweme_detail(root: object, *, source_aweme_id: str) -> dict[str, object] | None:
    root = normalize_page_state_root(root)
    if not isinstance(root, dict):
        return None

    if str(root.get("aweme_id") or "") == source_aweme_id:
        return root

    direct = root.get("aweme_detail")
    if isinstance(direct, dict) and str(direct.get("aweme_id") or "") == source_aweme_id:
        return direct

    data = root.get("data")
    if isinstance(data, dict):
        nested = pick_aweme_detail(data, source_aweme_id=source_aweme_id)
        if nested is not None:
            return nested

    aweme_list = root.get("aweme_list")
    if isinstance(aweme_list, list):
        for item in aweme_list:
            if isinstance(item, dict) and str(item.get("aweme_id") or "") == source_aweme_id:
                return item

    item_module = root.get("ItemModule")
    if isinstance(item_module, dict):
        item = item_module.get(source_aweme_id)
        if isinstance(item, dict) and str(item.get("aweme_id") or "") == source_aweme_id:
            return item

    return None


def normalize_page_state_root(root: object) -> dict[str, object] | None:
    if isinstance(root, dict):
        return root
    if not isinstance(root, str):
        return None

    candidates = [root]
    decoded = parse.unquote(root)
    if decoded != root:
        candidates.insert(0, decoded)

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


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


class DouyinAuthenticatedBrowserBridge:
    def __init__(
        self,
        *,
        run_applescript=default_run_applescript,
        timeout_seconds: int = 10,
        _sign_browser_detail_request=None,
    ) -> None:
        self._run_applescript = run_applescript
        self._timeout_seconds = max(timeout_seconds, 1)
        self._sign_browser_detail_request = _sign_browser_detail_request or sign_browser_detail_request

    def list_tabs(self) -> list[ChromeTab]:
        output = self._run_script(self._build_list_tabs_script())
        return parse_chrome_tab_listing(output)

    def extract_page_state(
        self,
        *,
        target_url: str,
        source_aweme_id: str,
        sign_base_url: str = "",
    ) -> dict[str, object]:
        tab = select_douyin_tab(self.list_tabs(), target_url=target_url)
        script = self._build_extract_page_state_script(tab=tab, source_aweme_id=source_aweme_id)
        raw_payload = self._run_script(script).strip()
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as error:
            raise PlatformAdapterError(
                code="douyin_browser_payload_invalid",
                message="浏览器桥接返回的内容不是合法 JSON",
                details={"error": str(error)},
            ) from error
        if not isinstance(payload, dict):
            raise PlatformAdapterError(
                code="douyin_browser_payload_invalid",
                message="浏览器桥接返回的页面态形状不合法",
            )
        try:
            extract_aweme_detail_from_page_state(payload, source_aweme_id=source_aweme_id)
        except PlatformAdapterError as error:
            if error.code != "douyin_content_not_found" or not sign_base_url:
                raise
            recovered = self._recover_aweme_detail_via_authenticated_request(
                tab=tab,
                source_aweme_id=source_aweme_id,
                sign_base_url=sign_base_url,
            )
            payload = dict(payload)
            payload["AWEME_DETAIL"] = recovered
            extract_aweme_detail_from_page_state(payload, source_aweme_id=source_aweme_id)
        return payload

    def _run_script(self, script: str) -> str:
        try:
            return self._invoke_run_applescript(script)
        except subprocess.TimeoutExpired as error:
            raise PlatformAdapterError(
                code="douyin_browser_command_failed",
                message="执行浏览器桥接脚本失败",
                details={"timeout_seconds": self._timeout_seconds, "error_type": error.__class__.__name__},
            ) from error
        except subprocess.CalledProcessError as error:
            stderr = error.stderr or ""
            if is_javascript_disabled_error(stderr):
                raise PlatformAdapterError(
                    code="douyin_browser_javascript_disabled",
                    message="Chrome 未启用 AppleScript JavaScript 执行能力",
                ) from error
            raise PlatformAdapterError(
                code="douyin_browser_command_failed",
                message="执行浏览器桥接脚本失败",
                details={"stderr": stderr, "returncode": error.returncode},
            ) from error
        except OSError as error:
            raise PlatformAdapterError(
                code="douyin_browser_command_failed",
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

    def _build_extract_page_state_script(self, *, tab: ChromeTab, source_aweme_id: str) -> str:
        js = json.dumps(self._build_in_page_javascript(source_aweme_id=source_aweme_id))
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

    def _recover_aweme_detail_via_authenticated_request(
        self,
        *,
        tab: ChromeTab,
        source_aweme_id: str,
        sign_base_url: str,
    ) -> dict[str, object]:
        context = self._read_detail_request_context(tab=tab)
        params = build_browser_detail_params(
            source_aweme_id=source_aweme_id,
            verify_fp=context.verify_fp,
            ms_token=context.ms_token,
            webid=context.webid,
        )
        params["a_bogus"] = self._sign_browser_detail_request(
            sign_base_url=sign_base_url,
            query_params=parse.urlencode(params),
            user_agent=context.user_agent,
            cookies=context.visible_cookies,
            timeout_seconds=self._timeout_seconds,
        )
        response = self._run_script(self._build_authenticated_detail_request_script(tab=tab, params=params)).strip()
        try:
            payload = json.loads(response)
        except json.JSONDecodeError as error:
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 请求返回非法 JSON",
                details={"error": str(error)},
            ) from error
        if not isinstance(payload, dict):
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 请求返回形状不合法",
            )
        status = payload.get("status")
        text = payload.get("text")
        if status != 200 or not isinstance(text, str) or not text:
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 请求未返回目标内容",
                details={"status": status},
            )
        try:
            detail_payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 响应不是合法 JSON",
                details={"status": status, "error": str(error)},
            ) from error
        if not isinstance(detail_payload, dict):
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 响应顶层必须是对象",
            )
        aweme_detail = detail_payload.get("aweme_detail")
        if not isinstance(aweme_detail, dict):
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 响应缺少 aweme_detail",
            )
        return aweme_detail

    def _read_detail_request_context(self, *, tab: ChromeTab) -> "BrowserDetailRequestContext":
        script = self._build_detail_request_context_script(tab=tab)
        raw_payload = self._run_script(script).strip()
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as error:
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 上下文不是合法 JSON",
                details={"error": str(error)},
            ) from error
        if not isinstance(payload, dict):
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 上下文形状不合法",
            )
        user_agent = payload.get("userAgent")
        verify_fp = payload.get("verifyFp")
        webid = payload.get("webid")
        ms_token = payload.get("xmst")
        visible_cookies = payload.get("cookies")
        if not all(isinstance(value, str) and value for value in (user_agent, verify_fp, webid, ms_token, visible_cookies)):
            raise PlatformAdapterError(
                code="douyin_content_not_found",
                message="浏览器 detail 上下文缺少必需字段",
            )
        return BrowserDetailRequestContext(
            user_agent=user_agent,
            verify_fp=verify_fp,
            webid=webid,
            ms_token=ms_token,
            visible_cookies=visible_cookies,
        )

    def _build_detail_request_context_script(self, *, tab: ChromeTab) -> str:
        js = json.dumps(
            """
(function() {
  const getCookie = (name) => {
    const matcher = new RegExp('(?:^|; )' + name.replace(/[$()*+.?[\\\\\\]^{|}]/g, '\\\\$&') + '=([^;]*)');
    const matched = document.cookie.match(matcher);
    return matched ? decodeURIComponent(matched[1]) : '';
  };
  return JSON.stringify({
    userAgent: navigator.userAgent,
    verifyFp: getCookie('s_v_web_id'),
    webid: JSON.parse(localStorage.getItem('__tea_cache_tokens_6383') || '{}').web_id || '',
    xmst: localStorage.getItem('xmst') || '',
    cookies: document.cookie
  });
})();
""".strip()
        )
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

    def _build_authenticated_detail_request_script(self, *, tab: ChromeTab, params: dict[str, object]) -> str:
        request_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?{parse.urlencode(params)}"
        js = json.dumps(
            f"""
(function() {{
  const xhr = new XMLHttpRequest();
  xhr.open('GET', {json.dumps(request_url)}, false);
  xhr.withCredentials = true;
  xhr.setRequestHeader('accept', 'application/json, text/plain, */*');
  xhr.send(null);
  return JSON.stringify({{ status: xhr.status, text: xhr.responseText || '' }});
}})();
""".strip()
        )
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

    def _build_in_page_javascript(self, *, source_aweme_id: str) -> str:
        serialized_aweme_id = json.dumps(source_aweme_id)
        return f"""
(function() {{
  const sourceAwemeId = {serialized_aweme_id};
  const payload = {{}};
  const candidateKeys = ["SSR_RENDER_DATA", "RENDER_DATA", "SIGI_STATE"];
  const normalizeRoot = (value) => {{
    if (!value) {{
      return null;
    }}
    if (value.tagName === "SCRIPT" && typeof value.textContent === "string") {{
      return value.textContent;
    }}
    if (typeof value === "object" || typeof value === "string") {{
      return value;
    }}
    return null;
  }};
  for (const key of candidateKeys) {{
    const value = normalizeRoot(window[key]);
    if (value !== null) {{
      payload[key] = value;
    }}
  }}
  const pick = (root) => {{
    if (!root || typeof root !== "object") {{
      return null;
    }}
    if (root.aweme_detail && root.aweme_detail.aweme_id === sourceAwemeId) {{
      return root.aweme_detail;
    }}
    if (root.data && typeof root.data === "object") {{
      const nested = pick(root.data);
      if (nested) {{
        return nested;
      }}
    }}
    if (Array.isArray(root.aweme_list)) {{
      return root.aweme_list.find((item) => item && item.aweme_id === sourceAwemeId) || null;
    }}
    const itemModule = root.ItemModule;
    if (itemModule && typeof itemModule === "object" && itemModule[sourceAwemeId]) {{
      return itemModule[sourceAwemeId];
    }}
    return null;
  }};
  return JSON.stringify(payload, (_key, value) => value === undefined ? null : value);
}})();
""".strip()


def is_javascript_disabled_error(stderr: str) -> bool:
    normalized = stderr.strip()
    return CHROME_JS_DISABLED_SNIPPET in normalized or "JavaScript from Apple Events is disabled." in normalized


@dataclass(frozen=True)
class BrowserDetailRequestContext:
    user_agent: str
    verify_fp: str
    webid: str
    ms_token: str
    visible_cookies: str


def build_browser_detail_params(
    *,
    source_aweme_id: str,
    verify_fp: str,
    ms_token: str,
    webid: str,
) -> dict[str, object]:
    return {
        "device_platform": "webapp",
        "aid": "6383",
        "channel": "channel_pc_web",
        "publish_video_strategy_type": 2,
        "update_version_code": 170400,
        "pc_client_type": 1,
        "version_code": "170400",
        "version_name": "17.4.0",
        "cookie_enabled": "true",
        "screen_width": 2560,
        "screen_height": 1440,
        "browser_language": "zh-CN",
        "browser_platform": "MacIntel",
        "browser_name": "Chrome",
        "browser_version": "146.0.0.0",
        "browser_online": "true",
        "engine_name": "Blink",
        "engine_version": "146.0.0.0",
        "os_name": "Mac+OS",
        "os_version": "10.15.7",
        "cpu_core_num": 10,
        "device_memory": 8,
        "platform": "PC",
        "downlink": 1.35,
        "effective_type": "3g",
        "round_trip_time": 350,
        "aweme_id": source_aweme_id,
        "verifyFp": verify_fp,
        "fp": verify_fp,
        "msToken": ms_token,
        "webid": webid,
    }


def sign_browser_detail_request(
    *,
    sign_base_url: str,
    query_params: str,
    user_agent: str,
    cookies: str,
    timeout_seconds: int,
) -> str:
    payload = json.dumps(
        {
            "uri": "/aweme/v1/web/aweme/detail/",
            "query_params": query_params,
            "user_agent": user_agent,
            "cookies": cookies,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = request.Request(
        f"{sign_base_url.rstrip('/')}/signsrv/v1/douyin/sign",
        data=payload,
        method="POST",
        headers={"content-type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=max(timeout_seconds, 1)) as response:
            raw = response.read().decode("utf-8")
    except (error.HTTPError, error.URLError, OSError) as exc:
        raise PlatformAdapterError(
            code="douyin_content_not_found",
            message="浏览器 detail 签名失败",
            details={"error_type": exc.__class__.__name__},
        ) from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlatformAdapterError(
            code="douyin_content_not_found",
            message="浏览器 detail 签名结果不是合法 JSON",
            details={"error": str(exc)},
        ) from exc
    if not isinstance(parsed, dict):
        raise PlatformAdapterError(
            code="douyin_content_not_found",
            message="浏览器 detail 签名结果形状不合法",
        )
    data = parsed.get("data")
    if not parsed.get("isok") or not isinstance(data, dict):
        raise PlatformAdapterError(
            code="douyin_content_not_found",
            message="浏览器 detail 签名结果缺少 data",
        )
    a_bogus = data.get("a_bogus")
    if not isinstance(a_bogus, str) or not a_bogus:
        raise PlatformAdapterError(
            code="douyin_content_not_found",
            message="浏览器 detail 签名缺少 a_bogus",
        )
    return a_bogus
