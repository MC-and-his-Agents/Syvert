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
from syvert.task_record import TaskRecordContractError, task_record_to_dict
from syvert.task_record_store import (
    LocalTaskRecordStore,
    TaskRecordPersistenceError,
    TaskRecordStoreError,
    default_task_record_store,
)


class CliArgumentError(ValueError):
    pass


class FailClosedArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliArgumentError(message)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] in {"-h", "--help"}:
        return build_root_parser().parse_args(args)
    if args and args[0] == "run":
        namespace = build_run_parser(prog="syvert.cli run").parse_args(args[1:])
        namespace.command = "run"
        return namespace
    if args and args[0] == "query":
        namespace = build_query_parser(prog="syvert.cli query").parse_args(args[1:])
        namespace.command = "query"
        return namespace
    namespace = build_legacy_parser().parse_args(args)
    namespace.command = "legacy_run"
    return namespace


def build_root_parser() -> FailClosedArgumentParser:
    parser = FailClosedArgumentParser(description="运行或查询 Syvert v0.3.0 本地单进程任务。")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "query"),
        help="可选子命令：`run` 运行任务，`query` 查询持久化任务记录。",
    )
    return parser


def build_legacy_parser() -> FailClosedArgumentParser:
    return build_run_like_parser(description="运行 Syvert v0.3.0 本地单进程任务。")


def build_run_parser(*, prog: str) -> FailClosedArgumentParser:
    return build_run_like_parser(description="运行 Syvert v0.3.0 本地单进程任务。", prog=prog)


def build_run_like_parser(description: str, *, prog: str | None = None) -> FailClosedArgumentParser:
    parser = FailClosedArgumentParser(description=description, prog=prog)
    parser.add_argument("--adapter", required=True, help="目标 adapter_key")
    parser.add_argument("--capability", required=True, help="任务 capability")
    parser.add_argument("--url", required=True, help="目标内容 URL")
    parser.add_argument(
        "--adapter-module",
        help="可选的 adapter 源，格式为 `module:attr`；attr 可以是 mapping 或返回 mapping 的可调用对象。",
    )
    return parser


def build_query_parser(*, prog: str) -> FailClosedArgumentParser:
    parser = FailClosedArgumentParser(description="查询 Syvert v0.3.0 的持久化任务记录。", prog=prog)
    parser.add_argument("--task-id", required=True, help="目标 task_id")
    return parser


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
    if args.command == "query":
        if not isinstance(args.task_id, str) or not args.task_id:
            return write_query_failure(
                task_id_factory=task_id_factory,
                stderr=err,
                error=invalid_input_error("invalid_cli_arguments", "`--task-id` 不得为空"),
            )
        return execute_query_command(
            args.task_id,
            task_id_factory=task_id_factory,
            stdout=out,
            stderr=err,
        )

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
        task_record_store=default_task_record_store(),
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


def execute_query_command(
    task_id: str,
    *,
    task_id_factory: Callable[[], str] | None = None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    store = default_task_record_store()
    root_error = validate_query_store_root(store)
    if root_error is not None:
        return write_query_failure(
            task_id=task_id,
            stderr=stderr,
            error=root_error,
        )

    try:
        record = store.load(task_id)
    except FileNotFoundError:
        return write_query_failure(
            task_id=task_id,
            stderr=stderr,
            error=invalid_input_error(
                "task_record_not_found",
                f"task_id `{task_id}` 对应的持久化任务记录不存在",
            ),
        )
    except (TaskRecordPersistenceError, TaskRecordStoreError, OSError) as error:
        return write_query_failure(
            task_id=task_id,
            stderr=stderr,
            error=runtime_contract_error(
                "task_record_unavailable",
                f"task_id `{task_id}` 对应的持久化任务记录不可用",
                details={"reason": str(error) or error.__class__.__name__},
            ),
        )

    try:
        payload = task_record_to_dict(record)
        serialized = json.dumps(payload, ensure_ascii=False)
    except (TaskRecordContractError, TypeError, ValueError) as error:
        return write_query_failure(
            task_id=task_id,
            adapter_key=record.request.adapter_key,
            capability=record.request.capability,
            stderr=stderr,
            error=runtime_contract_error(
                "task_record_unavailable",
                f"task_id `{task_id}` 对应的持久化任务记录不可用",
                details={"reason": str(error) or error.__class__.__name__},
            ),
        )

    stdout.write(serialized + "\n")
    return 0


def validate_query_store_root(store: LocalTaskRecordStore) -> dict[str, Any] | None:
    try:
        root = store.root
        if root.exists():
            if not root.is_dir():
                raise TaskRecordStoreError(f"任务记录存储根路径 `{root}` 不是目录")
            return None
        raise TaskRecordStoreError(f"任务记录存储根路径 `{root}` 不存在")
    except (TaskRecordStoreError, OSError) as error:
        return runtime_contract_error(
            "task_record_unavailable",
            "任务记录存储不可用",
            details={"reason": str(error) or error.__class__.__name__},
        )


def write_query_failure(
    *,
    stderr: TextIO,
    error: dict[str, Any],
    task_id: str | None = None,
    task_id_factory: Callable[[], str] | None = None,
    adapter_key: str = "",
    capability: str = "",
) -> int:
    resolved_task_id = task_id
    if not isinstance(resolved_task_id, str) or not resolved_task_id:
        resolved_task_id, task_id_error = resolve_task_id(task_id_factory)
        if task_id_error is not None:
            error = task_id_error
    envelope = failure_envelope(resolved_task_id, adapter_key, capability, error)
    stderr.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    return 1


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
    if args and args[0] == "query":
        return "", ""
    if args and args[0] == "run":
        args = args[1:]
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
