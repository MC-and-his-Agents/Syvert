from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any, Callable, Mapping, TextIO

from syvert.runtime import TaskRequest, execute_task


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 Syvert v0.1.0 本地单进程任务。")
    parser.add_argument("--adapter", required=True, help="目标 adapter_key")
    parser.add_argument("--capability", required=True, help="任务 capability")
    parser.add_argument("--url", required=True, help="目标内容 URL")
    parser.add_argument(
        "--adapter-module",
        help="可选的 adapter 源，格式为 `module:attr`；attr 可以是 mapping 或返回 mapping 的可调用对象。",
    )
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    *,
    adapters: Mapping[str, Any] | None = None,
    task_id_factory: Callable[[], str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    args = parse_args(argv)
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    resolved_adapters = adapters or load_adapters(args.adapter_module)
    envelope = execute_task(
        TaskRequest(
            adapter_key=args.adapter,
            capability=args.capability,
            input_url=args.url,
        ),
        adapters=resolved_adapters,
        task_id_factory=task_id_factory,
    )
    stream = out if envelope["status"] == "success" else err
    stream.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    return 0 if envelope["status"] == "success" else 1


def load_adapters(spec: str | None) -> Mapping[str, Any]:
    if not spec:
        return {}
    module_name, _, attr_name = spec.partition(":")
    if not module_name or not attr_name:
        raise SystemExit("`--adapter-module` 必须采用 `module:attr` 格式。")
    module = importlib.import_module(module_name)
    source = getattr(module, attr_name)
    resolved = source() if callable(source) else source
    if not isinstance(resolved, Mapping):
        raise SystemExit("`--adapter-module` 解析结果必须是 mapping。")
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())
