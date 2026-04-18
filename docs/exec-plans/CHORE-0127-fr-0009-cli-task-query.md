# CHORE-0127-fr-0009-cli-task-query 执行计划

## 关联信息

- item_key：`CHORE-0127-fr-0009-cli-task-query`
- Issue：`#142`
- item_type：`CHORE`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0009-cli-task-query-and-core-path/`
- 状态：`active`
- active 收口事项：`CHORE-0127-fr-0009-cli-task-query`

## 目标

- 在不扩张 `FR-0009` requirement 的前提下，为 CLI 落地 `query --task-id <id>` public surface，并把顶层入口重构为 `run/query`，同时保留 legacy 平铺执行入口兼容。

## 范围

- 本次纳入：
  - `syvert/cli.py`
  - 与 CLI query public surface 直接相关的测试
  - `docs/exec-plans/CHORE-0127-fr-0009-cli-task-query.md`
- 本次不纳入：
  - `FR-0008` durable schema 改写
  - 列表查询、筛选、摘要视图
  - `#143` 的端到端 same-path 证据收口

## 当前停点

- `issue-142-fr-0009-cli` 已作为 `#142` 的独立 implementation worktree 建立，且只保留 `syvert/cli.py`、`tests/runtime/test_cli.py` 与当前 exec-plan 的受控改动。
- 当前分支已经完成 `run/query` 顶层子命令、legacy 平铺执行入口兼容、query 成功输出完整 `TaskRecord` JSON，以及 `invalid_cli_arguments` / `task_record_not_found` / `task_record_unavailable` 的错误映射实现。
- `#141` formal spec 已由 PR `#154` 合入主干，`#142` 当前停点是把现有实现 rebasing 到最新 `origin/main`，完成实现门禁、受控开 PR 与 guardian merge gate。

## 下一步动作

- 将当前 `#142` 改动提交为独立 implementation checkpoint，并 rebase 到已包含 `#141` 的最新 `origin/main`。
- 运行 CLI / task-record 回归、adapter CLI 最小回归、`pr_scope_guard` 与 `open_pr.py --dry-run`。
- 同步 GitHub issue `#142` 的执行状态与当前事项上下文后，创建 implementation PR 并进入 guardian 审查与受控合并。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 建立最小 CLI query public surface，使 durable `TaskRecord` 可被显式查询。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0009` 的 CLI query 实现 Work Item。
- 阻塞：
  - `#143` 必须等待本事项合入主干后再建立 same-path closeout 现场。

## 已验证项

- 已核对 `#141` formal spec 已由 PR `#154` 合入主干，且 `#128` 的 formal spec 字段已收敛到已入库真相。
- `python3 -m unittest tests.runtime.test_cli tests.runtime.test_task_record tests.runtime.test_task_record_store`
  - 结果：通过（63 tests, OK）
- 已新增并本地通过的回归覆盖：
  - `run/query` 顶层子命令
  - legacy 平铺执行入口兼容
  - `query` 回读 `accepted` / `running` / `succeeded` / `failed`
  - `invalid_cli_arguments` / `task_record_not_found` / `task_record_unavailable`
  - 已加载 record 的输出失败回填 `record.request.adapter_key` / `capability`
  - `run` 与 legacy 平铺执行入口的共享 durable truth 一致性

## 未决风险

- 当前分支尚未 rebase 到包含 `#141` 的最新 `origin/main`；若 rebase 暴露同文件冲突，需要先按 formal spec 真相收敛，再进入 PR 流程。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 CLI 入口改动与 query public surface 相关测试。

## 最近一次 checkpoint 对应的 head SHA

- `3de165090c55a089c4785eead3b3d31321634564`
