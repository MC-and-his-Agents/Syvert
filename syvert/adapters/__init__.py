from collections.abc import Iterator, Mapping

from syvert.adapters.douyin import DouyinAdapter, build_adapters as build_douyin_adapters
from syvert.adapters.xhs import XhsAdapter, build_adapters as build_xhs_adapters


class AdapterBindingSources(Mapping[str, object]):
    def __init__(self, *sources: Mapping[str, object]) -> None:
        self._items: list[tuple[str, object]] = []
        for source in sources:
            self._items.extend(source.items())

    def __iter__(self) -> Iterator[str]:
        yielded: set[str] = set()
        for adapter_key, _adapter in self._items:
            if adapter_key in yielded:
                continue
            yielded.add(adapter_key)
            yield adapter_key

    def __len__(self) -> int:
        return len({adapter_key for adapter_key, _adapter in self._items})

    def __getitem__(self, key: str) -> object:
        for adapter_key, adapter in self._items:
            if adapter_key == key:
                return adapter
        raise KeyError(key)

    def items(self) -> Iterator[tuple[str, object]]:
        return iter(self._items)


def build_adapters() -> Mapping[str, object]:
    """Return adapter bindings for registry materialization."""
    return AdapterBindingSources(
        build_xhs_adapters(),
        build_douyin_adapters(),
    )


__all__ = ["XhsAdapter", "DouyinAdapter", "build_adapters"]
