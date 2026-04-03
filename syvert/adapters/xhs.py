from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib import error, parse, request

from syvert.runtime import CONTENT_DETAIL_BY_URL, PlatformAdapterError, TaskRequest


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


class XhsAdapter:
    adapter_key = "xhs"
    supported_capabilities = frozenset({CONTENT_DETAIL_BY_URL})

    def __init__(
        self,
        *,
        session_path: Path | None = None,
        session_provider: Callable[[Path], XhsSessionConfig] | None = None,
        sign_transport: SignTransport | None = None,
        detail_transport: DetailTransport | None = None,
    ) -> None:
        self._session_path = session_path or DEFAULT_XHS_SESSION_PATH
        self._session_provider = session_provider or load_session_config
        self._sign_transport = sign_transport or default_sign_transport
        self._detail_transport = detail_transport or default_detail_transport

    def execute(self, request: TaskRequest) -> dict[str, Any]:
        url_info = parse_xhs_detail_url(request.input.url)
        session = self._session_provider(self._session_path)
        body = build_detail_body(url_info)
        headers = self._build_headers(session, body)
        detail_response = self._fetch_detail(session, headers, body)
        note_card = extract_note_card(detail_response)
        normalized = normalize_note_card(note_card, request.input.url)
        return {"raw": detail_response, "normalized": normalized}

    def _build_headers(self, session: XhsSessionConfig, body: dict[str, Any]) -> dict[str, str]:
        if not session.sign_base_url:
            raise PlatformAdapterError(
                code="xhs_sign_unavailable",
                message="xhs sign_base_url 缺失",
                details={"session_path": str(self._session_path)},
            )
        sign_payload = {
            "uri": XHS_DETAIL_URI,
            "data": body,
            "cookies": session.cookies,
        }
        try:
            signed = dict(self._sign_transport(session.sign_base_url, sign_payload, session.timeout_seconds))
        except PlatformAdapterError:
            raise
        except Exception as exc:
            raise PlatformAdapterError(
                code="xhs_sign_unavailable",
                message="小红书签名服务不可用",
                details={"error_type": exc.__class__.__name__},
            ) from exc

        required_fields = ("x_s", "x_t", "x_s_common", "x_b3_traceid")
        for field in required_fields:
            value = signed.get(field)
            if not isinstance(value, str) or not value:
                raise PlatformAdapterError(
                    code="xhs_sign_unavailable",
                    message="小红书签名结果缺失必需字段",
                    details={"field": field},
                )

        return {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.xiaohongshu.com",
            "referer": "https://www.xiaohongshu.com/",
            "user-agent": session.user_agent,
            "cookie": session.cookies,
            "X-s": signed["x_s"],
            "X-t": signed["x_t"],
            "x-s-common": signed["x_s_common"],
            "X-B3-Traceid": signed["x_b3_traceid"],
        }

    def _fetch_detail(
        self,
        session: XhsSessionConfig,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> Mapping[str, Any]:
        try:
            response = self._detail_transport(
                url=f"{XHS_API_BASE_URL}{XHS_DETAIL_URI}",
                headers=headers,
                body=body,
                timeout_seconds=session.timeout_seconds,
            )
        except PlatformAdapterError:
            raise
        except Exception as exc:
            raise PlatformAdapterError(
                code="xhs_detail_request_failed",
                message="小红书 detail 请求失败",
                details={"error_type": exc.__class__.__name__},
            ) from exc
        if not isinstance(response, Mapping):
            raise PlatformAdapterError(
                code="xhs_detail_request_failed",
                message="小红书 detail 响应不是对象",
                details={},
            )
        return normalize_detail_response(response)


def build_adapters() -> dict[str, object]:
    return {"xhs": XhsAdapter()}


def parse_xhs_detail_url(url: str) -> XhsUrlInfo:
    parsed = parse.urlparse(url)
    host = parsed.netloc.lower()
    if host not in VALID_XHS_HOSTS:
        raise PlatformAdapterError(
            code="invalid_xhs_url",
            message="不是支持的小红书详情 URL",
            details={"url": url},
        )

    path_parts = [part for part in parsed.path.split("/") if part]
    note_id = ""
    if len(path_parts) >= 2 and path_parts[0] in {"explore", "discovery"}:
        note_id = path_parts[-1]
    if not note_id:
        raise PlatformAdapterError(
            code="invalid_xhs_url",
            message="无法从 URL 中解析 note_id",
            details={"url": url},
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


def optional_string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def coerce_timeout_seconds(value: Any) -> int:
    if value is None:
        return DEFAULT_TIMEOUT_SECONDS
    if isinstance(value, bool):
        return DEFAULT_TIMEOUT_SECONDS
    if isinstance(value, (int, float)):
        numeric = int(value)
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


def extract_note_card(detail_response: Mapping[str, Any]) -> Mapping[str, Any]:
    items = detail_response.get("items")
    if not isinstance(items, list) or not items:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书 detail 未返回内容",
            details={},
        )
    first = items[0]
    if not isinstance(first, Mapping):
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message="小红书 detail item 形状不合法",
            details={},
        )
    note_card = first.get("note_card")
    if not isinstance(note_card, Mapping) or not note_card:
        raise PlatformAdapterError(
            code="xhs_content_not_found",
            message="小红书 detail note_card 缺失",
            details={},
        )
    return note_card


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
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(float(stripped))
        except (ValueError, OverflowError):
            return None
    return None


def normalize_detail_response(response: Mapping[str, Any]) -> Mapping[str, Any]:
    items = response.get("items")
    if isinstance(items, list):
        return response

    success = response.get("success")
    if success is True:
        data = response.get("data")
        if isinstance(data, Mapping):
            return data
        raise PlatformAdapterError(
            code="xhs_detail_request_failed",
            message="小红书 detail 成功响应缺少 data",
            details={},
        )

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
            master_url = non_empty_string(item.get("master_url"))
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
