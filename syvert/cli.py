from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable, Mapping, TextIO

from syvert.runtime import TaskRequest, execute_task


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 Syvert v0.1.0 本地单进程任务。")
    parser.add_argument("--adapter", required=True, help="目标 adapter_key")
    parser.add_argument("--capability", required=True, help="任务 capability")
    parser.add_argument("--url", required=True, help="目标内容 URL")
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
    envelope = execute_task(
        TaskRequest(
            adapter_key=args.adapter,
            capability=args.capability,
            input_url=args.url,
        ),
        adapters=adapters or {},
        task_id_factory=task_id_factory,
    )
    stream = out if envelope["status"] == "success" else err
    stream.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    return 0 if envelope["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
