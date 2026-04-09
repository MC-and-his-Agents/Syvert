from syvert.adapters.douyin import DouyinAdapter, build_adapters as build_douyin_adapters
from syvert.adapters.xhs import XhsAdapter, build_adapters as build_xhs_adapters


def build_adapters() -> dict[str, object]:
    adapters: dict[str, object] = {}
    adapters.update(build_xhs_adapters())
    adapters.update(build_douyin_adapters())
    return adapters


__all__ = ["XhsAdapter", "DouyinAdapter", "build_adapters"]
