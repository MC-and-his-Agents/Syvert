from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from syvert.runtime import PlatformAdapterError


XHS_API_BASE_URL = "https://edith.xiaohongshu.com"
XHS_DETAIL_URI = "/api/sns/web/v1/feed"


SignTransport = Callable[[str, dict[str, Any], int], Mapping[str, Any]]
DetailTransport = Callable[..., Mapping[str, Any]]
PageTransport = Callable[..., str]
PageStateTransport = Callable[..., Mapping[str, Any]]


@dataclass(frozen=True)
class XhsProviderContext:
    session: Any
    parsed_target: Any


@dataclass(frozen=True)
class XhsProviderResult:
    raw_payload: Mapping[str, Any]
    platform_detail: Mapping[str, Any]


class NativeXhsProvider:
    def __init__(
        self,
        *,
        session_path: Path,
        api_base_url: str,
        detail_uri: str,
        sign_transport: SignTransport,
        detail_transport: DetailTransport,
        page_transport: PageTransport,
        page_state_transport: PageStateTransport,
        build_detail_body: Callable[[Any], dict[str, Any]],
        normalize_detail_response: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        extract_note_card: Callable[..., Mapping[str, Any]],
        extract_note_card_from_html_page: Callable[..., tuple[Mapping[str, Any], Mapping[str, Any]]],
        extract_note_card_from_page_state: Callable[..., tuple[Mapping[str, Any], Mapping[str, Any]]],
        choose_preferred_html_error: Callable[
            [PlatformAdapterError, PlatformAdapterError | None],
            PlatformAdapterError | None,
        ],
    ) -> None:
        self._session_path = session_path
        self._api_base_url = api_base_url
        self._detail_uri = detail_uri
        self._sign_transport = sign_transport
        self._detail_transport = detail_transport
        self._page_transport = page_transport
        self._page_state_transport = page_state_transport
        self._build_detail_body = build_detail_body
        self._normalize_detail_response = normalize_detail_response
        self._extract_note_card = extract_note_card
        self._extract_note_card_from_html_page = extract_note_card_from_html_page
        self._extract_note_card_from_page_state = extract_note_card_from_page_state
        self._choose_preferred_html_error = choose_preferred_html_error

    def fetch_content_detail(self, context: XhsProviderContext, input_url: str) -> XhsProviderResult:
        url_info = context.parsed_target
        body = self._build_detail_body(url_info)
        try:
            headers = self.build_headers(context.session, body)
            raw_response = self.fetch_detail(context.session, headers, body)
            detail_response = self._normalize_detail_response(raw_response)
            note_card = self._extract_note_card(detail_response, source_note_id=url_info.note_id)
        except PlatformAdapterError as exc:
            raw_response, note_card = self.recover_note_card_from_html(
                exc,
                session=context.session,
                input_url=input_url,
                source_note_id=url_info.note_id,
            )
        return XhsProviderResult(raw_payload=raw_response, platform_detail=note_card)

    def build_headers(self, session: Any, body: dict[str, Any]) -> dict[str, str]:
        if not session.sign_base_url:
            raise PlatformAdapterError(
                code="xhs_sign_unavailable",
                message="xhs sign_base_url 缺失",
                details={"session_path": str(self._session_path)},
            )
        sign_payload = {
            "uri": self._detail_uri,
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

    def fetch_detail(
        self,
        session: Any,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> Mapping[str, Any]:
        try:
            response = self._detail_transport(
                url=f"{self._api_base_url}{self._detail_uri}",
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
        return response

    def recover_note_card_from_html(
        self,
        original_error: PlatformAdapterError,
        *,
        session: Any,
        input_url: str,
        source_note_id: str,
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        if original_error.code not in {
            "xhs_detail_request_failed",
            "xhs_content_not_found",
            "xhs_sign_unavailable",
        }:
            raise original_error

        html_error: PlatformAdapterError | None = None
        try:
            html = self.fetch_html_page(session, input_url)
        except PlatformAdapterError as exc:
            html_error = exc
        else:
            try:
                return self._extract_note_card_from_html_page(html, source_note_id=source_note_id)
            except PlatformAdapterError as exc:
                html_error = exc

        try:
            page_state = self._page_state_transport(
                url=input_url,
                timeout_seconds=session.timeout_seconds,
                source_note_id=source_note_id,
                cookies=session.cookies,
                user_agent=session.user_agent,
            )
            return self._extract_note_card_from_page_state(
                page_state,
                source_note_id=source_note_id,
            )
        except PlatformAdapterError as exc:
            if exc.code == "xhs_browser_target_tab_missing":
                preferred_error = self._choose_preferred_html_error(original_error, html_error)
                if preferred_error is not None:
                    raise preferred_error
                raise original_error
            raise exc

    def fetch_html_page(self, session: Any, input_url: str) -> str:
        return self._page_transport(
            url=input_url,
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "referer": "https://www.xiaohongshu.com/",
                "user-agent": session.user_agent,
                "cookie": session.cookies,
            },
            timeout_seconds=session.timeout_seconds,
        )
