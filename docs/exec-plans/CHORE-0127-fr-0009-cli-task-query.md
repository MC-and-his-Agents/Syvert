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
  - `docs/exec-plans/artifacts/FR-0009-cli-query-and-core-path-verification-matrix.md`
  - `syvert/cli.py`
  - 与 CLI query public surface 直接相关的测试
  - `docs/exec-plans/CHORE-0127-fr-0009-cli-task-query.md`
- 本次不纳入：
  - `FR-0008` durable schema 改写
  - 列表查询、筛选、摘要视图
  - `#143` 的端到端 same-path 证据收口

## 当前停点

- `issue-142-fr-0009-cli` 已作为 `#142` 的独立 implementation worktree 建立，且只保留 `syvert/cli.py`、`tests/runtime/test_cli.py` 与当前 exec-plan 的受控改动。
- 当前分支已经完成 `run/query` 顶层子命令、legacy 平铺执行入口兼容、query 成功输出完整 `TaskRecord` JSON，以及 `invalid_cli_arguments` / `task_record_not_found` / `task_record_unavailable` 的 formal spec 错误映射实现。
- `#141` formal spec 已由 PR `#154` 合入主干，当前分支也已 rebase 到最新 `origin/main`。
- `#142` 当前停点是恢复推进补丁已提交为 checkpoint `51be04214fcb79fdfe0630d775bc1118c11cde48`，并已完成本地回归；下一步是推送到 PR `#156` 并重跑 guardian / merge gate。

## 下一步动作

- 提交本轮恢复推进补丁，并把 verification matrix、exec-plan、实现与测试一起推送到 PR `#156`。
- 同步 GitHub issue `#142` 与 PR `#156` 的执行真相，明确当前 PR 已进入“guardian findings recovered”状态。
- 在当前 head 上重跑 guardian 与 `merge_pr.py 156 --delete-branch --refresh-review`，如仍有阻断则先回填 matrix 再修。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 建立最小 CLI query public surface，使 durable `TaskRecord` 可被显式查询。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0009` 的 CLI query 实现 Work Item。
- 阻塞：
  - `#143` 必须等待本事项合入主干后再建立 same-path closeout 现场。

## 已验证项

- 已核对 `#141` formal spec 已由 PR `#154` 合入主干，且 `#128` 的 formal spec 字段已收敛到已入库真相。
- 已建立 `FR-0009` formal spec clause -> runtime/test 的 verification matrix carrier：`docs/exec-plans/artifacts/FR-0009-cli-query-and-core-path-verification-matrix.md`
- `python3 -m unittest tests.runtime.test_cli tests.runtime.test_task_record tests.runtime.test_task_record_store`
  - 结果：通过（65 tests, OK）
- `python3 -m unittest tests.runtime.test_xhs_adapter.XhsAdapterTests.test_cli_module_path_can_load_xhs_adapter_from_shared_registry`
  - 结果：通过（1 test, OK）
- 当前已验证项以 verification matrix 为准；`#142` 只负责矩阵中 `scope owner=#142` 的条目，`#143` 同路径闭环条目保持 `planned`。

## 未决风险

- 若继续只按 guardian 最新 finding 点修，而不按 verification matrix 全量对账，`#156` 仍可能因遗漏相邻负路径再次被驳回。
- 需要确保推送到 PR `#156` 的 head 与当前 exec-plan / verification matrix / guardian 复审绑定到同一提交，避免再次出现 review 真相分叉。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 CLI 入口改动与 query public surface 相关测试。

## 最近一次 checkpoint 对应的 head SHA

- `51be04214fcb79fdfe0630d775bc1118c11cde48`
