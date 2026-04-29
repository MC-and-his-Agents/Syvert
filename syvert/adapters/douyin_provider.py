from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib import parse

from syvert.runtime import PlatformAdapterError


DOUYIN_API_BASE_URL = "https://www.douyin.com"
DOUYIN_DETAIL_URI = "/aweme/v1/web/aweme/detail/"


SignTransport = Callable[[str, dict[str, Any], int], Mapping[str, Any]]
DetailTransport = Callable[..., Mapping[str, Any]]
PageStateTransport = Callable[..., Mapping[str, Any]]


@dataclass(frozen=True)
class DouyinProviderContext:
    session: Any
    parsed_target: Any


@dataclass(frozen=True)
class DouyinProviderResult:
    raw_payload: Mapping[str, Any]
    platform_detail: Mapping[str, Any]


class NativeDouyinProvider:
    def __init__(
        self,
        *,
        session_path: Path,
        api_base_url: str,
        detail_uri: str,
        sign_transport: SignTransport,
        detail_transport: DetailTransport,
        page_state_transport: PageStateTransport,
        build_detail_params: Callable[[Any, str], dict[str, Any]],
        build_detail_headers: Callable[[Any], dict[str, str]],
        normalize_detail_response: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        extract_aweme_detail_from_page_state: Callable[..., Mapping[str, Any]],
        synthesize_detail_response: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> None:
        self._session_path = session_path
        self._api_base_url = api_base_url
        self._detail_uri = detail_uri
        self._sign_transport = sign_transport
        self._detail_transport = detail_transport
        self._page_state_transport = page_state_transport
        self._build_detail_params = build_detail_params
        self._build_detail_headers = build_detail_headers
        self._normalize_detail_response = normalize_detail_response
        self._extract_aweme_detail_from_page_state = extract_aweme_detail_from_page_state
        self._synthesize_detail_response = synthesize_detail_response

    def fetch_content_detail(self, context: DouyinProviderContext, input_url: str) -> DouyinProviderResult:
        url_info = context.parsed_target
        try:
            params = self.build_detail_params(context.session, url_info)
            raw_response = self.fetch_detail(context.session, params)
            aweme_detail = self._normalize_detail_response(raw_response)
        except PlatformAdapterError as exc:
            raw_response, aweme_detail = self.recover_aweme_detail_from_page_state(
                exc,
                session=context.session,
                input_url=input_url,
                source_aweme_id=url_info.aweme_id,
            )
        return DouyinProviderResult(raw_payload=raw_response, platform_detail=aweme_detail)

    def build_detail_params(
        self,
        session: Any,
        url_info: Any,
    ) -> dict[str, Any]:
        if not session.sign_base_url:
            raise PlatformAdapterError(
                code="douyin_sign_unavailable",
                message="douyin sign_base_url 缺失",
                details={"session_path": str(self._session_path)},
            )
        params = self._build_detail_params(session, url_info.aweme_id)
        sign_payload = {
            "uri": self._detail_uri,
            "query_params": parse.urlencode(params),
            "user_agent": session.user_agent,
            "cookies": session.cookies,
        }
        try:
            signed = dict(self._sign_transport(session.sign_base_url, sign_payload, session.timeout_seconds))
        except PlatformAdapterError:
            raise
        except Exception as exc:
            raise PlatformAdapterError(
                code="douyin_sign_unavailable",
                message="抖音签名服务不可用",
                details={"error_type": exc.__class__.__name__},
            ) from exc
        a_bogus = signed.get("a_bogus")
        if not isinstance(a_bogus, str) or not a_bogus:
            raise PlatformAdapterError(
                code="douyin_sign_unavailable",
                message="抖音签名结果缺少 `a_bogus`",
                details={},
            )
        params["a_bogus"] = a_bogus
        return params

    def fetch_detail(
        self,
        session: Any,
        params: dict[str, Any],
    ) -> Mapping[str, Any]:
        try:
            response = self._detail_transport(
                url=f"{self._api_base_url}{self._detail_uri}",
                headers=self._build_detail_headers(session),
                params=params,
                timeout_seconds=session.timeout_seconds,
            )
        except PlatformAdapterError:
            raise
        except Exception as exc:
            raise PlatformAdapterError(
                code="douyin_detail_request_failed",
                message="抖音 detail 请求失败",
                details={"error_type": exc.__class__.__name__},
            ) from exc
        if not isinstance(response, Mapping):
            raise PlatformAdapterError(
                code="douyin_detail_request_failed",
                message="抖音 detail 响应不是对象",
                details={},
            )
        return response

    def recover_aweme_detail_from_page_state(
        self,
        original_error: PlatformAdapterError,
        *,
        session: Any,
        input_url: str,
        source_aweme_id: str,
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        if original_error.code not in {
            "douyin_detail_request_failed",
            "douyin_content_not_found",
            "douyin_sign_unavailable",
        }:
            raise original_error
        try:
            page_state = self._page_state_transport(
                url=input_url,
                timeout_seconds=session.timeout_seconds,
                source_aweme_id=source_aweme_id,
                cookies=session.cookies,
                user_agent=session.user_agent,
                sign_base_url=session.sign_base_url,
            )
            aweme_detail = self._extract_aweme_detail_from_page_state(page_state, source_aweme_id=source_aweme_id)
            return self._synthesize_detail_response(aweme_detail), aweme_detail
        except PlatformAdapterError as exc:
            if exc.code in {"douyin_browser_target_tab_missing", "douyin_content_not_found"}:
                raise original_error
            raise exc
