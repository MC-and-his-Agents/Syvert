from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
from typing import Any, Callable, Mapping
from urllib import error, parse, request

from syvert.registry import baseline_required_resource_requirement_declaration
from syvert.adapters.xhs_browser_bridge import XhsAuthenticatedBrowserBridge
from syvert.adapters.xhs_provider import NativeXhsProvider, XhsProviderContext
from syvert.runtime import AdapterExecutionContext, CONTENT_DETAIL, PlatformAdapterError


XHS_API_BASE_URL = "https://edith.xiaohongshu.com"
XHS_DETAIL_URI = "/api/sns/web/v1/feed"
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_XHS_SESSION_PATH = Path.home() / ".config" / "syvert" / "xhs.session.json"
VALID_XHS_HOSTS = frozenset(
    {
        "www.xiaohongshu.com",
        "xiaohongshu.com",
    }
)
@dataclass(frozen=True)
class XhsUrlInfo:
    note_id: str
    xsec_token: str
    xsec_source: str


@dataclass(frozen=True)
class XhsSessionConfig:
    cookies: str
    user_agent: str
    sign_base_url: str
    timeout_seconds: int


SignTransport = Callable[[str, dict[str, Any], int], Mapping[str, Any]]
DetailTransport = Callable[..., Mapping[str, Any]]
PageTransport = Callable[..., str]
PageStateTransport = Callable[..., Mapping[str, Any]]


class XhsAdapter:
    adapter_key = "xhs"
    supported_capabilities = frozenset({CONTENT_DETAIL})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    resource_requirement_declarations = (
        baseline_required_resource_requirement_declaration(
            adapter_key=adapter_key,
            capability=CONTENT_DETAIL,
        ),
    )

    def __init__(
        self,
        *,
        session_path: Path | None = None,
        session_provider: Callable[[Path], XhsSessionConfig] | None = None,
        sign_transport: SignTransport | None = None,
        detail_transport: DetailTransport | None = None,
        page_transport: PageTransport | None = None,
        page_state_transport: PageStateTransport | None = None,
        provider: Any | None = None,
    ) -> None:
        self._session_path = session_path or DEFAULT_XHS_SESSION_PATH
        self._session_provider = session_provider or load_session_config
        self._sign_transport = sign_transport or default_sign_transport
        self._detail_transport = detail_transport or default_detail_transport
        self._page_transport = page_transport or default_page_transport
        self._page_state_transport = page_state_transport or default_page_state_transport
        # Adapter-owned test seam; Core and registry never select providers.
        self._provider = provider or NativeXhsProvider(
            session_path=self._session_path,
            api_base_url=XHS_API_BASE_URL,
            detail_uri=XHS_DETAIL_URI,
            sign_transport=self._sign_transport,
            detail_transport=self._detail_transport,
            page_transport=self._page_transport,
            page_state_transport=self._page_state_transport,
            build_detail_body=build_detail_body,
            normalize_detail_response=normalize_detail_response,
            extract_note_card=extract_note_card,
            extract_note_card_from_html_page=extract_note_card_from_html_page,
            extract_note_card_from_page_state=extract_note_card_from_page_state,
            choose_preferred_html_error=choose_preferred_html_error,
        )

    def execute(self, request: AdapterExecutionContext) -> dict[str, Any]:
        context = resolve_execution_context(request=request)
        input_url = resolve_input_url(request=context)
        url_info = parse_xhs_detail_url(input_url)
        session = build_session_config_from_context(context)
        provider_result = self._provider.fetch_content_detail(
            XhsProviderContext(session=session, parsed_target=url_info),
            input_url,
        )
        normalized = normalize_note_card(provider_result.platform_detail, input_url)
        return {"raw": provider_result.raw_payload, "normalized": normalized}

    def _build_headers(self, session: XhsSessionConfig, body: dict[str, Any]) -> dict[str, str]:
        return self._provider.build_headers(session, body)

    def _fetch_detail(
        self,
        session: XhsSessionConfig,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> Mapping[str, Any]:
        return self._provider.fetch_detail(session, headers, body)

    def _recover_note_card_from_html(
        self,
        original_error: PlatformAdapterError,
        *,
        session: XhsSessionConfig,
        input_url: str,
        source_note_id: str,
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        return self._provider.recover_note_card_from_html(
            original_error,
            session=session,
            input_url=input_url,
            source_note_id=source_note_id,
        )

    def _fetch_html_page(self, session: XhsSessionConfig, input_url: str) -> str:
        return self._provider.fetch_html_page(session, input_url)


def build_adapters() -> dict[str, object]:
    return {"xhs": XhsAdapter()}


def resolve_execution_context(*, request: AdapterExecutionContext) -> AdapterExecutionContext:
    if type(request) is not AdapterExecutionContext:
        raise PlatformAdapterError(
            code="invalid_xhs_request",
            message="xhs adapter request 顶层形状不合法",
            details={"request_type": type(request).__name__},
            category="invalid_input",
        )
    if request.request.capability != CONTENT_DETAIL:
        raise PlatformAdapterError(
            code="invalid_xhs_request",
            message="xhs adapter 不支持该 capability family",
            details={"capability": request.request.capability},
            category="invalid_input",
        )
    if request.request.target_type != "url":
        raise PlatformAdapterError(
            code="invalid_xhs_request",
            message="xhs adapter 仅支持 target_type=url",
            details={"target_type": request.request.target_type},
            category="invalid_input",
        )
    if request.request.collection_mode != "hybrid":
        raise PlatformAdapterError(
            code="invalid_xhs_request",
            message="xhs adapter 仅支持 collection_mode=hybrid",
            details={"collection_mode": request.request.collection_mode},
            category="invalid_input",
        )
    return request


def resolve_input_url(*, request: AdapterExecutionContext) -> str:
    if type(request) is AdapterExecutionContext:
        return request.request.target_value
    raise PlatformAdapterError(
        code="invalid_xhs_request",
        message="xhs adapter request 顶层形状不合法",
        details={"request_type": type(request).__name__},
        category="invalid_input",
    )


def build_session_config_from_context(context: AdapterExecutionContext) -> XhsSessionConfig:
    resource_bundle = context.resource_bundle
    if resource_bundle is None:
        raise PlatformAdapterError(
            code="xhs_resource_bundle_missing",
            message="xhs adapter 需要 Core 注入 resource_bundle",
            details={},
            category="invalid_input",
        )
    account = resource_bundle.account
    if account is None:
        raise PlatformAdapterError(
            code="xhs_account_material_missing",
            message="xhs adapter 需要 account 资源",
            details={},
            category="invalid_input",
        )
    material = account.material
    if not isinstance(material, Mapping):
        raise PlatformAdapterError(
            code="xhs_account_material_missing",
            message="xhs account.material 必须是对象",
            details={"actual_type": type(material).__name__},
            category="invalid_input",
        )
    return XhsSessionConfig(
        cookies=require_material_string(material, "cookies", error_code="xhs_account_material_missing"),
        user_agent=require_material_string(material, "user_agent", error_code="xhs_account_material_missing"),
        sign_base_url=optional_string(material.get("sign_base_url")),
        timeout_seconds=coerce_timeout_seconds(material.get("timeout_seconds")),
    )


def parse_xhs_detail_url(url: str) -> XhsUrlInfo:
    parsed = parse.urlparse(url)
    host = parsed.netloc.lower()
    if host not in VALID_XHS_HOSTS:
        raise PlatformAdapterError(
            code="invalid_xhs_url",
            message="不是支持的小红书详情 URL",
            details={"url": url},
            category="invalid_input",
        )

    path_parts = [part for part in parsed.path.split("/") if part]
    note_id = ""
    if len(path_parts) == 2 and path_parts[0] == "explore":
        note_id = path_parts[1]
    if not note_id:
        raise PlatformAdapterError(
            code="invalid_xhs_url",
            message="无法从 URL 中解析 note_id",
            details={"url": url},
            category="invalid_input",
        )

    query = parse.parse_qs(parsed.query, keep_blank_values=True)
    return XhsUrlInfo(
        note_id=note_id,
        xsec_token=first_query_value(query, "xsec_token"),
        xsec_source=first_query_value(query, "xsec_source"),
    )


def first_query_value(query: Mapping[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""


def build_detail_body(url_info: XhsUrlInfo) -> dict[str, Any]:
    body: dict[str, Any] = {
        "source_note_id": url_info.note_id,
        "image_formats": ["jpg", "webp", "avif"],
        "extra": {"need_body_topic": 1},
    }
    if url_info.xsec_token:
        body["xsec_token"] = url_info.xsec_token
        body["xsec_source"] = url_info.xsec_source
    return body


def load_session_config(path: Path) -> XhsSessionConfig:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PlatformAdapterError(
            code="xhs_session_missing",
            message="小红书会话文件不存在",
            details={"session_path": str(path)},
        ) from exc
    except OSError as exc:
        raise PlatformAdapterError(
            code="xhs_session_missing",
            message="小红书会话文件无法读取",
            details={"session_path": str(path), "error_type": exc.__class__.__name__},
        ) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlatformAdapterError(
            code="xhs_session_missing",
            message="小红书会话文件不是合法 JSON",
            details={"session_path": str(path)},
        ) from exc

    if not isinstance(data, Mapping):
        raise PlatformAdapterError(
            code="xhs_session_missing",
            message="小红书会话文件顶层必须是对象",
            details={"session_path": str(path)},
        )

    cookies = require_string(data, "cookies", path, error_code="xhs_session_missing")
    user_agent = require_string(data, "user_agent", path, error_code="xhs_session_missing")
    sign_base_url = optional_string(data.get("sign_base_url"))
    timeout_seconds = coerce_timeout_seconds(data.get("timeout_seconds"))
    return XhsSessionConfig(
        cookies=cookies,
        user_agent=user_agent,
        sign_base_url=sign_base_url,
        timeout_seconds=timeout_seconds,
    )


def require_string(
    data: Mapping[str, Any],
    field: str,
    path: Path,
    *,
    error_code: str,
) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise PlatformAdapterError(
            code=error_code,
            message=f"小红书会话文件缺少 `{field}`",
            details={"session_path": str(path), "field": field},
        )
    return value


def require_material_string(
    data: Mapping[str, Any],
    field: str,
    *,
    error_code: str,
) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise PlatformAdapterError(
            code=error_code,
            message=f"xhs account.material 缺少 `{field}`",
            details={"field": field},
            category="invalid_input",
        )
    return value


def optional_string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def coerce_timeout_seconds(value: Any) -> int:
    if value is None:
        return DEFAULT_TIMEOUT_SECONDS
    if isinstance(value, bool):
        return DEFAULT_TIMEOUT_SECONDS
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return DEFAULT_TIMEOUT_SECONDS
        try:
            numeric = int(value)
        except (OverflowError, ValueError):
            return DEFAULT_TIMEOUT_SECONDS
        return numeric if numeric > 0 else DEFAULT_TIMEOUT_SECONDS
    if isinstance(value, str) and value.isdigit():
        numeric = int(value)
        return numeric if numeric > 0 else DEFAULT_TIMEOUT_SECONDS
    return DEFAULT_TIMEOUT_SECONDS


def default_sign_transport(base_url: str, payload: dict[str, Any], timeout_seconds: int) -> Mapping[str, Any]:
    response = post_json(
        f"{base_url.rstrip('/')}/signsrv/v1/xhs/sign",
        payload,
        headers={"content-type": "application/json"},
        timeout_seconds=timeout_seconds,
    )
    if not response.get("isok"):
        raise PlatformAdapterError(
            code="xhs_sign_unavailable",
            message="小红书签名服务返回失败",
            details={"response": dict(response)},
        )
    data = response.get("data")
    if not isinstance(data, Mapping):
        raise PlatformAdapterError(
            code="xhs_sign_unavailable",
            message="小红书签名服务返回缺少 data",
            details={},
        )
    return data


def default_detail_transport(
    *,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout_seconds: int,
) -> Mapping[str, Any]:
    return post_json(url, body, headers=headers, timeout_seconds=timeout_seconds)


def default_page_transport(
    *,
    url: str,
    headers: dict[str, str],
    timeout_seconds: int,
) -> str:
    req = request.Request(url, method="GET")
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise PlatformAdapterError(
            code="xhs_content_not_found" if exc.code == 404 else "xhs_detail_request_failed",
            message=f"HTTP {exc.code}",
            details={"url": url, "response_body": body_text[:500]},
        ) from exc
    except error.URLError as exc:
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message="页面请求失败",
            details={"url": url, "reason": str(exc.reason)},
        ) from exc


def default_page_state_transport(
    *,
    url: str,
    timeout_seconds: int,
    source_note_id: str = "",
    cookies: str = "",
    user_agent: str = "",
) -> Mapping[str, Any]:
    del cookies, user_agent
    return XhsAuthenticatedBrowserBridge(timeout_seconds=timeout_seconds).extract_page_state(
        target_url=url,
        source_note_id=source_note_id,
    )


def choose_preferred_html_error(
    original_error: PlatformAdapterError,
    html_error: PlatformAdapterError | None,
) -> PlatformAdapterError | None:
    if html_error is None:
        return None
    if is_structured_platform_error(original_error):
        return None
    if html_error.code == "xhs_content_not_found":
        return html_error
    if html_error.code == "xhs_detail_request_failed" and original_error.code != "xhs_content_not_found":
        return html_error
    if html_error.code == "xhs_sign_unavailable" and original_error.code == "xhs_sign_unavailable":
        return html_error
    return None


def is_structured_platform_error(error: PlatformAdapterError) -> bool:
    return error.code == "xhs_detail_request_failed" and any(
        key in error.details for key in ("platform_code", "platform_message", "platform_data")
    )


def post_json(
    url: str,
    body: Mapping[str, Any],
    *,
    headers: Mapping[str, str],
    timeout_seconds: int,
) -> Mapping[str, Any]:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=payload, method="POST")
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise PlatformAdapterError(
            code="xhs_detail_request_failed" if "/feed" in url else "xhs_sign_unavailable",
            message=f"HTTP {exc.code}",
            details={"url": url, "response_body": body_text[:500]},
        ) from exc
    except error.URLError as exc:
        raise PlatformAdapterError(
            code="xhs_detail_request_failed" if "/feed" in url else "xhs_sign_unavailable",
            message="网络请求失败",
            details={"url": url, "reason": str(exc.reason)},
        ) from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlatformAdapterError(
            code="xhs_detail_request_failed" if "/feed" in url else "xhs_sign_unavailable",
            message="响应不是合法 JSON",
            details={"url": url},
        ) from exc
    if not isinstance(parsed, Mapping):
        raise PlatformAdapterError(
            code="xhs_detail_request_failed" if "/feed" in url else "xhs_sign_unavailable",
            message="响应顶层必须为对象",
            details={"url": url},
        )
    return parsed


def extract_note_card_from_html_page(
    html: str,
    *,
    source_note_id: str | None = None,
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    state = extract_html_initial_state(html)
    return extract_note_card_from_page_state(
        state,
        source_note_id=source_note_id,
    )


def extract_note_card_from_page_state(
    state: Mapping[str, Any],
    *,
    source_note_id: str | None = None,
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    note_state = state.get("note")
    if not isinstance(note_state, Mapping):
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书页面缺少 note 状态",
            details={},
        )

    note_detail_map = note_state.get("noteDetailMap")
    if not isinstance(note_detail_map, Mapping) or not note_detail_map:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书页面缺少 noteDetailMap",
            details={},
        )

    current_note_id = first_non_empty_string(
        note_state.get("currentNoteId"),
        note_state.get("firstNoteId"),
        source_note_id,
    )
    selected_key, selected_entry = select_html_note_entry(
        note_detail_map,
        source_note_id=source_note_id,
        current_note_id=current_note_id,
    )
    note = selected_entry.get("note")
    if not isinstance(note, Mapping) or not note:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书页面未返回 note 数据",
            details={"note_key": selected_key},
        )

    note_card = coerce_html_note_to_note_card(note)
    note_id = non_empty_string(note_card.get("note_id"))
    if not note_id:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书页面未返回有效 note_id",
            details={"note_key": selected_key},
        )
    if source_note_id and note_id != source_note_id:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书页面返回的 note_id 与目标不一致",
            details={"source_note_id": source_note_id, "actual_note_id": note_id},
        )

    return dict(state), note_card


def extract_html_initial_state(html: str) -> Mapping[str, Any]:
    match = re.search(r"window\.__INITIAL_STATE__=(.+?)</script>", html, re.S)
    if match is None:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书页面缺少 __INITIAL_STATE__",
            details={},
        )

    state_text = replace_javascript_undefined_tokens(match.group(1)).strip()
    if state_text.endswith(";"):
        state_text = state_text.rstrip(";").rstrip()
    try:
        parsed = json.loads(state_text)
    except json.JSONDecodeError as exc:
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message="小红书页面状态不是合法 JSON",
            details={},
        ) from exc
    if not isinstance(parsed, Mapping):
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message="小红书页面状态顶层必须是对象",
            details={},
        )
    return parsed


def replace_javascript_undefined_tokens(text: str) -> str:
    result: list[str] = []
    string_delimiter = ""
    escaping = False
    identifier_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$")
    token = "undefined"
    token_length = len(token)
    index = 0

    while index < len(text):
        char = text[index]
        if string_delimiter:
            result.append(char)
            if escaping:
                escaping = False
            elif char == "\\":
                escaping = True
            elif char == string_delimiter:
                string_delimiter = ""
            index += 1
            continue
        if char in {'"', "'"}:
            string_delimiter = char
            result.append(char)
            index += 1
            continue
        if text.startswith(token, index):
            prev_char = text[index - 1] if index > 0 else ""
            next_index = index + token_length
            next_char = text[next_index] if next_index < len(text) else ""
            if prev_char not in identifier_chars and next_char not in identifier_chars:
                result.append("null")
                index += token_length
                continue
        result.append(char)
        index += 1

    return "".join(result)


def select_html_note_entry(
    note_detail_map: Mapping[str, Any],
    *,
    source_note_id: str | None = None,
    current_note_id: str | None = None,
) -> tuple[str, Mapping[str, Any]]:
    if source_note_id:
        entry = note_detail_map.get(source_note_id)
        if isinstance(entry, Mapping):
            return source_note_id, entry
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书页面未返回目标 note",
            details={"source_note_id": source_note_id},
        )

    if current_note_id:
        entry = note_detail_map.get(current_note_id)
        if isinstance(entry, Mapping):
            return current_note_id, entry

    for key, entry in note_detail_map.items():
        if not isinstance(entry, Mapping):
            continue
        note = entry.get("note")
        if isinstance(note, Mapping) and note:
            return str(key), entry

    raise PlatformAdapterError(
        code="xhs_content_not_found",
        message="小红书页面未返回目标 note",
        details={},
    )


def coerce_html_note_to_note_card(note: Mapping[str, Any]) -> dict[str, Any]:
    user = note.get("user")
    interact_info = note.get("interactInfo")
    image_list = note.get("imageList")
    video = note.get("video")
    cover = note.get("cover")

    user_mapping = user if isinstance(user, Mapping) else {}
    interact_mapping = interact_info if isinstance(interact_info, Mapping) else {}
    image_items = image_list if isinstance(image_list, list) else []
    video_mapping = video if isinstance(video, Mapping) else {}
    cover_mapping = cover if isinstance(cover, Mapping) else {}

    return {
        "note_id": first_non_empty_string(note.get("noteId"), note.get("note_id")) or "",
        "type": first_non_empty_string(note.get("type")) or "",
        "title": string_value(note.get("title")) or "",
        "desc": string_value(note.get("desc")) or "",
        "time": note.get("time"),
        "user": {
            "user_id": first_non_empty_string(user_mapping.get("userId"), user_mapping.get("user_id")),
            "nickname": first_non_empty_string(user_mapping.get("nickname")),
            "avatar": first_non_empty_string(
                user_mapping.get("avatar"),
                user_mapping.get("avatarUrl"),
                user_mapping.get("image"),
            ),
        },
        "interact_info": {
            "liked_count": interact_mapping.get("likedCount"),
            "comment_count": interact_mapping.get("commentCount"),
            "share_count": interact_mapping.get("shareCount"),
            "collected_count": interact_mapping.get("collectedCount"),
        },
        "image_list": [
            coerce_html_image_item(image)
            for image in image_items
            if isinstance(image, Mapping)
        ],
        "video": video_mapping,
        "cover": cover_mapping,
    }


def coerce_html_image_item(image: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "url_default": first_non_empty_string(
            image.get("urlDefault"),
            image.get("url_default"),
            image.get("url"),
        ),
        "url": first_non_empty_string(image.get("url"), image.get("urlPre")),
        "stream": image.get("stream") if isinstance(image.get("stream"), Mapping) else {},
        "live_photo": image.get("livePhoto"),
    }


def extract_note_card(
    detail_response: Mapping[str, Any],
    *,
    source_note_id: str | None = None,
) -> Mapping[str, Any]:
    items = detail_response.get("items")
    if not isinstance(items, list) or not items:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书 detail 未返回内容",
            details={},
        )
    first_valid_note_card: Mapping[str, Any] | None = None
    saw_invalid_item = False
    for item in items:
        if not isinstance(item, Mapping):
            saw_invalid_item = True
            continue
        note_card = item.get("note_card")
        if not isinstance(note_card, Mapping) or not note_card:
            continue
        if first_valid_note_card is None:
            first_valid_note_card = note_card
        if source_note_id:
            note_id = non_empty_string(note_card.get("note_id"))
            if note_id == source_note_id:
                return note_card

    if first_valid_note_card is not None and not source_note_id:
        return first_valid_note_card
    if first_valid_note_card is not None and source_note_id:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书 detail 未返回目标内容",
            details={"source_note_id": source_note_id},
        )
    if saw_invalid_item:
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message="小红书 detail item 形状不合法",
            details={},
        )
    raise PlatformAdapterError(
        code="xhs_content_not_found",
        message="小红书 detail note_card 缺失",
        details={},
    )


def normalize_note_card(note_card: Mapping[str, Any], input_url: str) -> dict[str, Any]:
    note_id = non_empty_string(note_card.get("note_id"))
    if not note_id:
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message="小红书 detail 缺少 note_id",
            details={},
        )

    user = note_card.get("user")
    interact_info = note_card.get("interact_info")
    image_list = note_card.get("image_list")
    cover = note_card.get("cover")
    video = note_card.get("video")

    user_mapping = user if isinstance(user, Mapping) else {}
    interact_mapping = interact_info if isinstance(interact_info, Mapping) else {}
    image_items = image_list if isinstance(image_list, list) else []
    cover_mapping = cover if isinstance(cover, Mapping) else {}
    video_mapping = video if isinstance(video, Mapping) else {}

    canonical_url = f"https://www.xiaohongshu.com/explore/{note_id}" or input_url
    image_urls = extract_image_urls(image_items)
    video_url = extract_video_url(video_mapping, image_items)
    cover_url = first_non_empty_string(
        cover_mapping.get("url_default"),
        cover_mapping.get("url"),
        image_urls[0] if image_urls else None,
    )

    return {
        "platform": "xhs",
        "content_id": note_id,
        "content_type": infer_content_type(note_card, image_urls, video_url),
        "canonical_url": canonical_url if canonical_url else input_url,
        "title": string_value(note_card.get("title")) or "",
        "body_text": string_value(note_card.get("desc")) or "",
        "published_at": normalize_published_at(note_card.get("time")),
        "author": {
            "author_id": nullable_non_empty_string(user_mapping.get("user_id")),
            "display_name": nullable_non_empty_string(user_mapping.get("nickname")),
            "avatar_url": nullable_string(
                first_non_empty_string(
                    user_mapping.get("avatar"),
                    user_mapping.get("image"),
                )
            ),
        },
        "stats": {
            "like_count": nullable_int(interact_mapping.get("liked_count")),
            "comment_count": nullable_int(interact_mapping.get("comment_count")),
            "share_count": nullable_int(interact_mapping.get("share_count")),
            "collect_count": nullable_int(interact_mapping.get("collected_count")),
        },
        "media": {
            "cover_url": nullable_string(cover_url),
            "video_url": nullable_string(video_url),
            "image_urls": image_urls,
        },
    }


def infer_content_type(note_card: Mapping[str, Any], image_urls: list[str], video_url: str | None) -> str:
    note_type = non_empty_string(note_card.get("type")).lower()
    if note_type == "video":
        return "video"
    if video_url and image_urls:
        return "mixed_media"
    if video_url:
        return "video"
    if image_urls:
        return "image_post"
    return "unknown"


def extract_image_urls(image_items: list[Any]) -> list[str]:
    urls: list[str] = []
    for image in image_items:
        if not isinstance(image, Mapping):
            continue
        url = first_non_empty_string(image.get("url_default"), image.get("url"))
        if url:
            urls.append(url)
    return urls


def extract_video_url(video_mapping: Mapping[str, Any], image_items: list[Any]) -> str | None:
    consumer = video_mapping.get("consumer")
    if isinstance(consumer, Mapping):
        origin_video_key = first_non_empty_string(
            consumer.get("origin_video_key"),
            consumer.get("originVideoKey"),
        )
        if origin_video_key:
            return f"https://sns-video-bd.xhscdn.com/{origin_video_key}"

    video_stream_url = extract_stream_video_url(video_mapping)
    if video_stream_url:
        return video_stream_url

    for image in image_items:
        if not isinstance(image, Mapping):
            continue
        image_stream_url = extract_stream_video_url(image)
        if image_stream_url:
            return image_stream_url
        live_photo = image.get("live_photo")
        if isinstance(live_photo, Mapping):
            live_photo_url = extract_stream_video_url(live_photo)
            if live_photo_url:
                return live_photo_url
    return None


def normalize_published_at(value: Any) -> str | None:
    if value is None:
        return None
    numeric: float | None = None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped:
            try:
                numeric = float(stripped)
            except ValueError:
                numeric = None
    if numeric is None:
        return None
    if not math.isfinite(numeric):
        return None
    seconds = numeric / 1000 if numeric >= 100_000_000_000 else numeric
    try:
        return (
            datetime.fromtimestamp(seconds, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (OverflowError, OSError, ValueError):
        return None


def nullable_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            numeric = float(stripped)
        except (ValueError, OverflowError):
            return None
        if not math.isfinite(numeric):
            return None
        return int(numeric)
    return None


def normalize_detail_response(response: Mapping[str, Any]) -> Mapping[str, Any]:
    success = response.get("success")
    if success is False or "code" in response or "msg" in response:
        details: dict[str, Any] = {}
        if "code" in response:
            details["platform_code"] = response.get("code")
        platform_message = non_empty_string(response.get("msg"))
        if platform_message:
            details["platform_message"] = platform_message
        data = response.get("data")
        if isinstance(data, Mapping) and data:
            details["platform_data"] = dict(data)
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message=platform_message or "小红书 detail 请求失败",
            details=details,
        )

    if success is True:
        data = response.get("data")
        if isinstance(data, Mapping):
            return data
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message="小红书 detail 成功响应缺少 data",
            details={},
        )

    items = response.get("items")
    if isinstance(items, list):
        return response

    return response


def extract_stream_video_url(container: Mapping[str, Any]) -> str | None:
    stream = container.get("stream")
    if isinstance(stream, Mapping):
        stream_url = extract_h264_master_url(stream)
        if stream_url:
            return stream_url

    media = container.get("media")
    if isinstance(media, Mapping):
        media_stream = media.get("stream")
        if isinstance(media_stream, Mapping):
            media_stream_url = extract_h264_master_url(media_stream)
            if media_stream_url:
                return media_stream_url

    return None


def extract_h264_master_url(stream: Mapping[str, Any]) -> str | None:
    h264 = stream.get("h264")
    if isinstance(h264, list):
        for item in h264:
            if not isinstance(item, Mapping):
                continue
            master_url = first_non_empty_string(item.get("master_url"), item.get("masterUrl"))
            if master_url:
                return master_url
    return None


def string_value(value: Any) -> str:
    return value if isinstance(value, str) else ""


def non_empty_string(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def nullable_non_empty_string(value: Any) -> str | None:
    normalized = non_empty_string(value)
    return normalized or None


def nullable_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def first_non_empty_string(*values: Any) -> str | None:
    for value in values:
        normalized = non_empty_string(value)
        if normalized:
            return normalized
    return None
