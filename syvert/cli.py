from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any, Callable, Mapping, TextIO

from syvert.runtime import (
    TaskInput,
    TaskRequest,
    execute_task_with_record,
    failure_envelope,
    invalid_input_error,
    resolve_task_id,
    runtime_contract_error,
)


class CliArgumentError(ValueError):
    pass


class FailClosedArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliArgumentError(message)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FailClosedArgumentParser(description="运行 Syvert v0.1.0 本地单进程任务。")
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
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        args = parse_args(argv)
    except CliArgumentError as error:
        task_id, task_id_error = resolve_task_id(task_id_factory)
        adapter_key, capability = extract_cli_context(argv)
        envelope_error = task_id_error or invalid_input_error("invalid_cli_arguments", str(error))
        envelope = failure_envelope(task_id, adapter_key, capability, envelope_error)
        err.write(json.dumps(envelope, ensure_ascii=False) + "\n")
        return 1
    request = TaskRequest(
        adapter_key=args.adapter,
        capability=args.capability,
        input=TaskInput(url=args.url),
    )
    try:
        resolved_adapters = adapters if adapters is not None else load_adapters(args.adapter_module)
    except Exception as error:
        task_id, task_id_error = resolve_task_id(task_id_factory)
        if task_id_error is not None:
            envelope = failure_envelope(
                task_id,
                request.adapter_key,
                request.capability,
                task_id_error,
            )
            err.write(json.dumps(envelope, ensure_ascii=False) + "\n")
            return 1
        envelope = failure_envelope(
            task_id,
            request.adapter_key,
            request.capability,
            runtime_contract_error(
                "adapter_loader_error",
                str(error) or error.__class__.__name__,
            ),
        )
        err.write(json.dumps(envelope, ensure_ascii=False) + "\n")
        return 1
    envelope = execute_task_with_record(
        request,
        adapters=resolved_adapters,
        task_id_factory=task_id_factory,
    ).envelope
    stream = out if envelope["status"] == "success" else err
    try:
        payload = json.dumps(envelope, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        fallback_task_id = envelope.get("task_id")
        if not isinstance(fallback_task_id, str) or not fallback_task_id:
            fallback_task_id, _ = resolve_task_id(None)
        envelope = failure_envelope(
            fallback_task_id,
            request.adapter_key,
            request.capability,
            runtime_contract_error(
                "envelope_not_json_serializable",
                "CLI 输出结果无法序列化为 JSON",
                details={"error_type": error.__class__.__name__},
            ),
        )
        payload = json.dumps(envelope, ensure_ascii=False)
        stream = err
    stream.write(payload + "\n")
    return 0 if envelope["status"] == "success" else 1


def load_adapters(spec: str | None) -> Mapping[str, Any]:
    if not spec:
        return {}
    module_name, _, attr_name = spec.partition(":")
    if not module_name or not attr_name:
        raise ValueError("`--adapter-module` 必须采用 `module:attr` 格式。")
    module = importlib.import_module(module_name)
    source = getattr(module, attr_name)
    resolved = source() if callable(source) else source
    if not isinstance(resolved, Mapping):
        raise ValueError("`--adapter-module` 解析结果必须是 mapping。")
    return resolved


def extract_cli_context(argv: list[str] | None) -> tuple[str, str]:
    args = list(argv) if argv is not None else sys.argv[1:]
    adapter_key = extract_cli_option(args, "--adapter")
    capability = extract_cli_option(args, "--capability")
    return adapter_key, capability


def extract_cli_option(argv: list[str], option: str) -> str:
    equals_prefix = f"{option}="
    for index, token in enumerate(argv):
        if token == option:
            if index + 1 >= len(argv):
                return ""
            value = argv[index + 1]
            if not isinstance(value, str) or value.startswith("--"):
                return ""
            return value
        if isinstance(token, str) and token.startswith(equals_prefix):
            value = token[len(equals_prefix) :]
            return value if isinstance(value, str) else ""
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
