from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib import error, parse, request

from syvert.adapter_capability_requirement import baseline_adapter_capability_requirement
from syvert.registry import baseline_multi_profile_resource_requirement_declaration
from syvert.adapters.douyin_browser_bridge import extract_aweme_detail_from_page_state
from syvert.adapters.douyin_browser_bridge import DouyinAuthenticatedBrowserBridge
from syvert.adapters.douyin_provider import DouyinProviderContext, NativeDouyinProvider
from syvert.runtime import AdapterExecutionContext, CONTENT_DETAIL, PlatformAdapterError


DOUYIN_API_BASE_URL = "https://www.douyin.com"
DOUYIN_DETAIL_URI = "/aweme/v1/web/aweme/detail/"
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_DOUYIN_SESSION_PATH = Path.home() / ".config" / "syvert" / "douyin.session.json"
VALID_DOUYIN_HOSTS = frozenset({"www.douyin.com", "douyin.com"})
VALID_IESDOUYIN_HOSTS = frozenset({"www.iesdouyin.com", "iesdouyin.com"})


@dataclass(frozen=True)
class DouyinUrlInfo:
    aweme_id: str
    canonical_url: str


@dataclass(frozen=True)
class DouyinSessionConfig:
    cookies: str
    user_agent: str
    verify_fp: str
    ms_token: str
    webid: str
    sign_base_url: str
    timeout_seconds: int


SignTransport = Callable[[str, dict[str, Any], int], Mapping[str, Any]]
DetailTransport = Callable[..., Mapping[str, Any]]
PageStateTransport = Callable[..., Mapping[str, Any]]


class DouyinAdapter:
    adapter_key = "douyin"
    supported_capabilities = frozenset({CONTENT_DETAIL})
    supported_targets = frozenset({"url"})
    supported_collection_modes = frozenset({"hybrid"})
    _content_detail_resource_requirement = baseline_multi_profile_resource_requirement_declaration(
        adapter_key=adapter_key,
        capability=CONTENT_DETAIL,
    )
    resource_requirement_declarations = (
        _content_detail_resource_requirement,
    )
    capability_requirement_declarations = (
        baseline_adapter_capability_requirement(
            adapter_key=adapter_key,
            resource_requirement=_content_detail_resource_requirement,
        ),
    )

    def __init__(
        self,
        *,
        session_path: Path | None = None,
        session_provider: Callable[[Path], DouyinSessionConfig] | None = None,
        sign_transport: SignTransport | None = None,
        detail_transport: DetailTransport | None = None,
        page_state_transport: PageStateTransport | None = None,
        provider: Any | None = None,
    ) -> None:
        self._session_path = session_path or DEFAULT_DOUYIN_SESSION_PATH
        self._session_provider = session_provider or load_session_config
        self._sign_transport = sign_transport or default_sign_transport
        self._detail_transport = detail_transport or default_detail_transport
        self._page_state_transport = page_state_transport or default_page_state_transport
        # Adapter-owned test seam; Core and registry never select providers.
        self._provider = provider or NativeDouyinProvider(
            session_path=self._session_path,
            api_base_url=DOUYIN_API_BASE_URL,
            detail_uri=DOUYIN_DETAIL_URI,
            sign_transport=self._sign_transport,
            detail_transport=self._detail_transport,
            page_state_transport=self._page_state_transport,
            build_detail_params=build_detail_params,
            build_detail_headers=build_detail_headers,
            normalize_detail_response=normalize_detail_response,
            extract_aweme_detail_from_page_state=extract_aweme_detail_from_page_state,
            synthesize_detail_response=synthesize_detail_response,
        )

    def execute(self, request: AdapterExecutionContext) -> dict[str, Any]:
        context = resolve_execution_context(request=request)
        input_url = resolve_input_url(request=context)
        url_info = parse_douyin_detail_url(input_url)
        session = build_session_config_from_context(context)
        provider_result = self._provider.fetch_content_detail(
            DouyinProviderContext(session=session, parsed_target=url_info),
            input_url,
        )
        normalized = normalize_aweme_detail(provider_result.platform_detail, canonical_url=url_info.canonical_url)
        return {"raw": provider_result.raw_payload, "normalized": normalized}

    def _build_detail_params(
        self,
        session: DouyinSessionConfig,
        url_info: DouyinUrlInfo,
    ) -> dict[str, Any]:
        return self._provider.build_detail_params(session, url_info)

    def _fetch_detail(
        self,
        session: DouyinSessionConfig,
        params: dict[str, Any],
    ) -> Mapping[str, Any]:
        return self._provider.fetch_detail(session, params)

    def _recover_aweme_detail_from_page_state(
        self,
        original_error: PlatformAdapterError,
        *,
        session: DouyinSessionConfig,
        input_url: str,
        source_aweme_id: str,
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        return self._provider.recover_aweme_detail_from_page_state(
            original_error,
            session=session,
            input_url=input_url,
            source_aweme_id=source_aweme_id,
        )


def build_adapters() -> dict[str, object]:
    return {"douyin": DouyinAdapter()}


def resolve_execution_context(*, request: AdapterExecutionContext) -> AdapterExecutionContext:
    if type(request) is not AdapterExecutionContext:
        raise PlatformAdapterError(
            code="invalid_douyin_request",
            message="douyin adapter request 顶层形状不合法",
            details={"request_type": type(request).__name__},
            category="invalid_input",
        )
    if request.request.capability != CONTENT_DETAIL:
        raise PlatformAdapterError(
            code="invalid_douyin_request",
            message="douyin adapter 不支持该 capability family",
            details={"capability": request.request.capability},
            category="invalid_input",
        )
    if request.request.target_type != "url":
        raise PlatformAdapterError(
            code="invalid_douyin_request",
            message="douyin adapter 仅支持 target_type=url",
            details={"target_type": request.request.target_type},
            category="invalid_input",
        )
    if request.request.collection_mode != "hybrid":
        raise PlatformAdapterError(
            code="invalid_douyin_request",
            message="douyin adapter 仅支持 collection_mode=hybrid",
            details={"collection_mode": request.request.collection_mode},
            category="invalid_input",
        )
    return request


def resolve_input_url(*, request: AdapterExecutionContext) -> str:
    if type(request) is AdapterExecutionContext:
        return request.request.target_value
    raise PlatformAdapterError(
        code="invalid_douyin_request",
        message="douyin adapter request 顶层形状不合法",
        details={"request_type": type(request).__name__},
        category="invalid_input",
    )


def build_session_config_from_context(context: AdapterExecutionContext) -> DouyinSessionConfig:
    resource_bundle = context.resource_bundle
    if resource_bundle is None:
        raise PlatformAdapterError(
            code="douyin_resource_bundle_missing",
            message="douyin adapter 需要 Core 注入 resource_bundle",
            details={},
            category="invalid_input",
        )
    account = resource_bundle.account
    if account is None:
        raise PlatformAdapterError(
            code="douyin_account_material_missing",
            message="douyin adapter 需要 account 资源",
            details={},
            category="invalid_input",
        )
    material = account.material
    if not isinstance(material, Mapping):
        raise PlatformAdapterError(
            code="douyin_account_material_missing",
            message="douyin account.material 必须是对象",
            details={"actual_type": type(material).__name__},
            category="invalid_input",
        )
    return DouyinSessionConfig(
        cookies=require_material_string(material, "cookies", error_code="douyin_account_material_missing"),
        user_agent=require_material_string(material, "user_agent", error_code="douyin_account_material_missing"),
        verify_fp=optional_string(material.get("verify_fp")),
        ms_token=optional_string(material.get("ms_token")),
        webid=optional_string(material.get("webid")),
        sign_base_url=optional_string(material.get("sign_base_url")),
        timeout_seconds=coerce_timeout_seconds(material.get("timeout_seconds")),
    )


def parse_douyin_detail_url(url: str) -> DouyinUrlInfo:
    parsed = parse.urlparse(url)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]
    aweme_id = ""

    if host in VALID_DOUYIN_HOSTS and len(path_parts) == 2 and path_parts[0] == "video":
        aweme_id = path_parts[1]
    elif host in VALID_IESDOUYIN_HOSTS and len(path_parts) >= 3 and path_parts[0] == "share" and path_parts[1] == "video":
        aweme_id = path_parts[2]
    elif host == "v.douyin.com":
        raise PlatformAdapterError(
            code="invalid_douyin_url",
            message="暂不支持抖音短链，需先解析到详情 URL",
            details={"url": url},
            category="invalid_input",
        )
    else:
        raise PlatformAdapterError(
            code="invalid_douyin_url",
            message="不是支持的抖音详情 URL",
            details={"url": url},
            category="invalid_input",
        )

    if not aweme_id.isdigit():
        raise PlatformAdapterError(
            code="invalid_douyin_url",
            message="无法从 URL 中解析 aweme_id",
            details={"url": url},
            category="invalid_input",
        )
    return DouyinUrlInfo(
        aweme_id=aweme_id,
        canonical_url=f"https://www.douyin.com/video/{aweme_id}",
    )


def load_session_config(path: Path) -> DouyinSessionConfig:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PlatformAdapterError(
            code="douyin_session_missing",
            message="抖音会话文件不存在",
            details={"session_path": str(path)},
        ) from exc
    except OSError as exc:
        raise PlatformAdapterError(
            code="douyin_session_missing",
            message="抖音会话文件无法读取",
            details={"session_path": str(path), "error_type": exc.__class__.__name__},
        ) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlatformAdapterError(
            code="douyin_session_missing",
            message="抖音会话文件不是合法 JSON",
            details={"session_path": str(path)},
        ) from exc

    if not isinstance(data, Mapping):
        raise PlatformAdapterError(
            code="douyin_session_missing",
            message="抖音会话文件顶层必须是对象",
            details={"session_path": str(path)},
        )

    return DouyinSessionConfig(
        cookies=require_string(data, "cookies", path),
        user_agent=require_string(data, "user_agent", path),
        verify_fp=optional_string(data.get("verify_fp")),
        ms_token=optional_string(data.get("ms_token")),
        webid=optional_string(data.get("webid")),
        sign_base_url=optional_string(data.get("sign_base_url")),
        timeout_seconds=coerce_timeout_seconds(data.get("timeout_seconds")),
    )


def require_string(data: Mapping[str, Any], field: str, path: Path) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise PlatformAdapterError(
            code="douyin_session_missing",
            message=f"抖音会话文件缺少 `{field}`",
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
            message=f"douyin account.material 缺少 `{field}`",
            details={"field": field},
            category="invalid_input",
        )
    return value


def optional_string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def coerce_timeout_seconds(value: Any) -> int:
    if value is None or isinstance(value, bool):
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


def build_detail_headers(session: DouyinSessionConfig) -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "cookie": session.cookies,
        "referer": "https://www.douyin.com/",
        "user-agent": session.user_agent,
    }


def build_detail_params(session: DouyinSessionConfig, aweme_id: str) -> dict[str, Any]:
    missing_fields = [
        field
        for field, value in (
            ("verify_fp", session.verify_fp),
            ("ms_token", session.ms_token),
            ("webid", session.webid),
        )
        if not value
    ]
    if missing_fields:
        raise PlatformAdapterError(
            code="douyin_sign_unavailable",
            message="抖音会话缺少 API 请求所需字段",
            details={"missing_fields": missing_fields},
        )
    params: dict[str, Any] = {
        "device_platform": "webapp",
        "aid": "6383",
        "channel": "channel_pc_web",
        "pc_client_type": 1,
        "version_code": "170400",
        "version_name": "17.4.0",
        "cookie_enabled": "true",
        "browser_platform": "MacIntel",
        "browser_name": "Chrome",
        "browser_online": "true",
        "engine_name": "Blink",
        "os_name": "Mac+OS",
        "platform": "PC",
        "downlink": 4.45,
        "effective_type": "4g",
        "round_trip_time": 100,
        "aweme_id": aweme_id,
        "verifyFp": session.verify_fp,
        "fp": session.verify_fp,
        "msToken": session.ms_token,
        "webid": session.webid,
    }
    return params


def synthesize_detail_response(aweme_detail: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status_code": 0,
        "aweme_detail": dict(aweme_detail),
    }


def default_sign_transport(base_url: str, payload: dict[str, Any], timeout_seconds: int) -> Mapping[str, Any]:
    response = post_json(
        f"{base_url.rstrip('/')}/signsrv/v1/douyin/sign",
        payload,
        headers={"content-type": "application/json"},
        timeout_seconds=timeout_seconds,
    )
    if not response.get("isok"):
        raise PlatformAdapterError(
            code="douyin_sign_unavailable",
            message="抖音签名服务返回失败",
            details={"response": dict(response)},
        )
    data = response.get("data")
    if not isinstance(data, Mapping):
        raise PlatformAdapterError(
            code="douyin_sign_unavailable",
            message="抖音签名服务返回缺少 data",
            details={},
        )
    return data


def default_detail_transport(
    *,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
    timeout_seconds: int,
) -> Mapping[str, Any]:
    query = parse.urlencode(params)
    req = request.Request(f"{url}?{query}", method="GET")
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise PlatformAdapterError(
            code="douyin_detail_request_failed" if exc.code != 404 else "douyin_content_not_found",
            message=f"HTTP {exc.code}",
            details={"url": url, "response_body": body_text[:500]},
        ) from exc
    except error.URLError as exc:
        raise PlatformAdapterError(
            code="douyin_detail_request_failed",
            message="网络请求失败",
            details={"url": url, "reason": str(exc.reason)},
        ) from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlatformAdapterError(
            code="douyin_detail_request_failed",
            message="响应不是合法 JSON",
            details={"url": url},
        ) from exc
    if not isinstance(parsed, Mapping):
        raise PlatformAdapterError(
            code="douyin_detail_request_failed",
            message="响应顶层必须是对象",
            details={"url": url},
        )
    return parsed


def default_page_state_transport(
    *,
    url: str,
    timeout_seconds: int,
    source_aweme_id: str = "",
    cookies: str = "",
    user_agent: str = "",
    sign_base_url: str = "",
) -> Mapping[str, Any]:
    del cookies, user_agent
    return DouyinAuthenticatedBrowserBridge(timeout_seconds=timeout_seconds).extract_page_state(
        target_url=url,
        source_aweme_id=source_aweme_id,
        sign_base_url=sign_base_url,
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
            code="douyin_sign_unavailable",
            message=f"HTTP {exc.code}",
            details={"url": url, "response_body": body_text[:500]},
        ) from exc
    except error.URLError as exc:
        raise PlatformAdapterError(
            code="douyin_sign_unavailable",
            message="网络请求失败",
            details={"url": url, "reason": str(exc.reason)},
        ) from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlatformAdapterError(
            code="douyin_sign_unavailable",
            message="响应不是合法 JSON",
            details={"url": url},
        ) from exc
    if not isinstance(parsed, Mapping):
        raise PlatformAdapterError(
            code="douyin_sign_unavailable",
            message="响应顶层必须是对象",
            details={"url": url},
        )
    return parsed


def normalize_detail_response(response: Mapping[str, Any]) -> Mapping[str, Any]:
    status_code = response.get("status_code", 0)
    if status_code not in (0, "0", None):
        raise PlatformAdapterError(
            code="douyin_detail_request_failed",
            message=first_non_empty_string(response.get("status_msg")) or "抖音 detail 返回失败",
            details={
                "platform_code": status_code,
                "platform_message": first_non_empty_string(response.get("status_msg")),
            },
        )
    aweme_detail = response.get("aweme_detail")
    if not isinstance(aweme_detail, Mapping) or not aweme_detail:
        raise PlatformAdapterError(
            code="douyin_content_not_found",
            message="抖音 detail 响应缺少 aweme_detail",
            details={},
        )
    return aweme_detail


def normalize_aweme_detail(aweme_detail: Mapping[str, Any], *, canonical_url: str) -> dict[str, Any]:
    aweme_id = first_non_empty_string(aweme_detail.get("aweme_id"))
    if not aweme_id:
        raise PlatformAdapterError(
            code="douyin_content_not_found",
            message="抖音 detail 缺少 aweme_id",
            details={},
        )
    author = aweme_detail.get("author") if isinstance(aweme_detail.get("author"), Mapping) else {}
    statistics = aweme_detail.get("statistics") if isinstance(aweme_detail.get("statistics"), Mapping) else {}
    video = aweme_detail.get("video") if isinstance(aweme_detail.get("video"), Mapping) else {}
    image_urls = extract_image_urls(aweme_detail)
    video_url = first_media_url(
        video.get("play_addr_h264"),
        video.get("play_addr"),
        video.get("download_addr"),
    )
    cover_url = first_media_url(
        video.get("cover"),
        video.get("origin_cover"),
        video.get("cover_original_scale"),
        author.get("avatar_thumb"),
    )
    return {
        "platform": "douyin",
        "content_id": aweme_id,
        "content_type": determine_content_type(aweme_detail, video_url=video_url, image_urls=image_urls),
        "canonical_url": canonical_url,
        "title": first_non_empty_string(aweme_detail.get("preview_title"), aweme_detail.get("desc"), ""),
        "body_text": string_or_empty(aweme_detail.get("desc")),
        "published_at": coerce_timestamp_to_rfc3339(aweme_detail.get("create_time")),
        "author": {
            "author_id": nullable_string(author.get("uid")),
            "display_name": nullable_string(author.get("nickname")),
            "avatar_url": nullable_string(first_media_url(author.get("avatar_thumb"))),
        },
        "stats": {
            "like_count": nullable_int(statistics.get("digg_count")),
            "comment_count": nullable_int(statistics.get("comment_count")),
            "share_count": nullable_int(statistics.get("share_count")),
            "collect_count": nullable_int(statistics.get("collect_count")),
        },
        "media": {
            "cover_url": nullable_string(cover_url),
            "video_url": nullable_string(video_url),
            "image_urls": image_urls,
        },
    }


def determine_content_type(
    aweme_detail: Mapping[str, Any],
    *,
    video_url: str,
    image_urls: list[str],
) -> str:
    has_video = bool(video_url)
    has_images = bool(image_urls)
    if has_video and has_images:
        return "mixed_media"
    if has_images:
        return "image_post"
    if has_video:
        return "video"
    if aweme_detail.get("image_post_info"):
        return "image_post"
    return "unknown"


def extract_image_urls(aweme_detail: Mapping[str, Any]) -> list[str]:
    candidates = aweme_detail.get("images")
    if isinstance(candidates, list):
        urls = [first_media_url(item) for item in candidates]
        return [url for url in urls if url]
    image_post_info = aweme_detail.get("image_post_info")
    if isinstance(image_post_info, Mapping):
        images = image_post_info.get("images")
        if isinstance(images, list):
            urls = [first_media_url(item.get("display_image"), item.get("owner_watermark_image"), item) for item in images]
            return [url for url in urls if url]
    return []


def first_media_url(*candidates: Any) -> str:
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            url_list = candidate.get("url_list")
            if isinstance(url_list, list):
                for value in url_list:
                    if isinstance(value, str) and value:
                        return value
            for key in ("main_url", "fallback_url", "backup_url"):
                value = candidate.get(key)
                if isinstance(value, str) and value:
                    return value
    return ""


def first_non_empty_string(*candidates: Any) -> str:
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return ""


def string_or_empty(value: Any) -> str:
    return value if isinstance(value, str) else ""


def nullable_string(value: Any) -> str | None:
    if isinstance(value, str):
        return value or None
    return None


def nullable_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        if value.is_integer():
            return int(value)
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
        return None
    return None


def coerce_timestamp_to_rfc3339(value: Any) -> str | None:
    timestamp = nullable_int(value)
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (OverflowError, OSError, ValueError):
        return None
