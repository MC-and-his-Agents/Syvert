# FR-0009 CLI query and core path verification matrix

## 关联信息

- FR：`#128`
- formal spec：`docs/specs/FR-0009-cli-task-query-and-core-path/`
- 当前 implementation Work Item：`#142 / CHORE-0127-fr-0009-cli-task-query`
- 后续 same-path Work Item：`#143 / CHORE-0128-fr-0009-cli-core-path-persistence-closeout`
- 当前主 PR：`#156`

## 使用规则

- 本矩阵是 `FR-0009` 在 `#142/#143` 之间的唯一 contract-to-test carrier。
- `scope owner=#142` 的条目必须在 `#156` 合入前实现、测试并回填状态。
- `scope owner=#143` 的条目只允许在 `#142` 合入后进入执行回合。
- guardian 新 finding 若属于 `FR-0009` contract，必须先回填到本矩阵，再继续修复。

| spec clause | scope owner | runtime/code path | expected stdout/stderr | expected exit code | expected error fields | test name | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `query --task-id <id>` 成功回读 durable success record | `#142` | `parse_args()` -> `execute_query_command()` -> `store.load()` -> `task_record_to_dict()` | `stdout=完整 TaskRecord JSON` / `stderr=""` | `0` | `n/a` | `test_query_subcommand_returns_persisted_success_record` | `implemented` |
| `query` 可回读 `accepted` record | `#142` | `execute_query_command()` success path | `stdout=完整 TaskRecord JSON` / `stderr=""` | `0` | `n/a` | `test_query_subcommand_returns_accepted_record` | `implemented` |
| `query` 可回读 `running` record | `#142` | `execute_query_command()` success path | `stdout=完整 TaskRecord JSON` / `stderr=""` | `0` | `n/a` | `test_query_subcommand_returns_running_record` | `implemented` |
| `query` 可回读 persisted failed record | `#142` | `execute_query_command()` success path | `stdout=完整 TaskRecord JSON` / `stderr=""` | `0` | `n/a` | `test_query_subcommand_returns_persisted_failed_record` | `implemented` |
| `query` 缺少 `--task-id` 时使用 fallback task_id 并返回 invalid cli arguments | `#142` | `main()` parse failure -> `recover_cli_failure_context()` -> `resolve_task_id()` | `stdout=""` / `stderr=failed envelope` | `1` | `code=invalid_cli_arguments`, `category=invalid_input`, `adapter_key=""`, `capability=""`, `task_id=fallback` | `test_query_subcommand_returns_invalid_cli_arguments_when_task_id_missing` | `implemented` |
| malformed `query` argv 若仍可恢复 `--task-id`，必须回显该 task_id | `#142` | `main()` parse failure -> `recover_cli_failure_context()` | `stdout=""` / `stderr=failed envelope` | `1` | `code=invalid_cli_arguments`, `category=invalid_input`, `adapter_key=""`, `capability=""`, `task_id=<recovered>` | `test_query_subcommand_parse_failure_preserves_recoverable_task_id` | `implemented` |
| `query` 参数错误且 fallback task_id 生成失败时，必须优先返回 invalid task id | `#142` | `main()` parse failure -> `resolve_task_id()` | `stdout=""` / `stderr=failed envelope` | `1` | `code=invalid_task_id`, `category=runtime_contract`, `adapter_key=""`, `capability=""` | `test_query_subcommand_parse_failure_returns_invalid_task_id_when_fallback_task_id_generation_fails` | `implemented` |
| unknown `task_id` 返回 task record not found | `#142` | `execute_query_command()` -> `store.load()` raises `FileNotFoundError` | `stdout=""` / `stderr=failed envelope` | `1` | `code=task_record_not_found`, `category=invalid_input`, `task_id=<requested>`, `adapter_key=""`, `capability=""` | `test_query_subcommand_returns_not_found_for_unknown_task_id` | `implemented` |
| invalid marker 返回 task record unavailable | `#142` | `execute_query_command()` -> `store.load()` raises persistence/store error | `stdout=""` / `stderr=failed envelope` | `1` | `code=task_record_unavailable`, `category=runtime_contract`, `task_id=<requested>`, `adapter_key=""`, `capability=""` | `test_query_subcommand_returns_unavailable_for_invalid_marker` | `implemented` |
| damaged JSON 返回 task record unavailable | `#142` | `execute_query_command()` -> `store.load()` raises persistence/store error | `stdout=""` / `stderr=failed envelope` | `1` | `code=task_record_unavailable`, `category=runtime_contract`, `task_id=<requested>`, `adapter_key=""`, `capability=""` | `test_query_subcommand_returns_unavailable_for_invalid_json_record` | `implemented` |
| contract-invalid record 返回 task record unavailable | `#142` | `execute_query_command()` -> `store.load()` raises persistence/store error | `stdout=""` / `stderr=failed envelope` | `1` | `code=task_record_unavailable`, `category=runtime_contract`, `task_id=<requested>`, `adapter_key=""`, `capability=""` | `test_query_subcommand_returns_unavailable_for_contract_invalid_record` | `implemented` |
| store root 不可用返回 task record unavailable | `#142` | `validate_query_store_root()` | `stdout=""` / `stderr=failed envelope` | `1` | `code=task_record_unavailable`, `category=runtime_contract`, `task_id=<requested>`, `adapter_key=""`, `capability=""` | `test_query_subcommand_returns_unavailable_when_store_root_is_missing` | `implemented` |
| record 已加载后共享序列化失败，必须 fail-closed 并回填 record context | `#142` | `execute_query_command()` post-load serialization branch | `stdout=""` / `stderr=failed envelope` | `1` | `code=task_record_unavailable`, `category=runtime_contract`, `task_id=<record.task_id>`, `adapter_key=<record.request.adapter_key>`, `capability=<record.request.capability>` | `test_query_subcommand_uses_record_context_when_loaded_record_fails_to_serialize` | `implemented` |
| record 已加载后 stdout 写出失败，必须 fail-closed 并回填 record context | `#142` | `execute_query_command()` post-load output branch | `stdout=""` / `stderr=failed envelope` | `1` | `code=task_record_unavailable`, `category=runtime_contract`, `task_id=<record.task_id>`, `adapter_key=<record.request.adapter_key>`, `capability=<record.request.capability>` | `test_query_subcommand_uses_record_context_when_loaded_record_cannot_be_written_to_stdout` | `implemented` |
| `run` 子命令成功输出 shared success envelope | `#142` | `parse_args()` -> `execute_task_with_record()` | `stdout=success envelope` / `stderr=""` | `0` | `n/a` | `test_run_subcommand_writes_success_envelope_to_stdout` | `implemented` |
| legacy 平铺执行入口 parse failure 继续保留 shared failed envelope 行为 | `#142` | `main()` legacy parse failure -> `extract_cli_context()` | `stdout=""` / `stderr=failed envelope` | `1` | `code=invalid_cli_arguments`, `category=invalid_input`, recoverable `adapter_key` / `capability` preserved | `test_cli_fails_closed_for_missing_required_arguments`, `test_cli_parse_failure_preserves_adapter_key_from_equals_syntax`, `test_cli_parse_failure_does_not_consume_next_flag_as_adapter_value` | `implemented` |
| `run` 后 `query` 必须等于 `task_record_to_dict(store.load(task_id))` | `#143` | `run` -> shared store -> `query` | `stdout=完整 TaskRecord JSON` / `stderr=""` | `0` | `n/a` | `test_run_subcommand_persists_record_that_query_reads_from_shared_store` | `implemented` |
| legacy run 与 `query` 必须回读同一 durable truth | `#143` | legacy run path -> shared store -> `query` | `stdout=完整 TaskRecord JSON` / `stderr=""` | `0` | `n/a` | `test_legacy_entrypoint_persists_record_that_query_reads_from_shared_store` | `implemented` |
| `query` 不得消费 shadow file / shadow payload | `#143` | `execute_query_command()` -> `default_task_record_store().load()` -> `task_record_to_dict()` | `stdout=task_record_to_dict(record)` / `stderr=""` | `0` | `n/a` | `test_query_subcommand_reads_loaded_record_via_shared_store_and_shared_serializer` | `implemented` |
