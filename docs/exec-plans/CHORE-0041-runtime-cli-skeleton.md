# CHORE-0041-runtime-cli-skeleton 执行计划

## 关联信息

- Issue：`#41`
- item_key：`CHORE-0041-runtime-cli-skeleton`
- item_type：`CHORE`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0002-content-detail-runtime-v0-1/spec.md`
- active 收口事项：`CHORE-0041-runtime-cli-skeleton`

## 目标

- 推进 `#41` 的 runtime / CLI skeleton 到可受控合并状态，并将本文件作为 `#44` 当前实现轮次的 active 审查追溯入口。

## 范围

- 本次纳入：
  - 本地单进程 `runtime + CLI` 最小执行骨架
  - 统一成功/失败 envelope 与 fail-closed 约束
  - `guardian` 阻断项的实现侧收口（含 CLI loader failure 的 `task_id_factory` 一致性）
- 本次不纳入：
  - 真实 adapter 联调
  - HTTP API / 队列 / 多进程 / 调度能力

## 当前停点

- `FR-0002` formal spec 已合入 `main`。
- `#41` 的实现工作在分支 `issue-41-runtime-local-single-process-executor-and-cli-skeleton` 推进。
- 最近一次实现 checkpoint 已推进到 `83e4c7c4ecd8759d86255e57859a76537dda0fac`，已收口 runtime 输入结构与 `task_id` 严格校验。
- 下一步进入审查态补件：刷新 PR `#44` 正文验证区块，并在当前 head 上重新执行 guardian。

## 下一步动作

- 刷新 PR `#44` 正文中的验证与 head SHA。
- 在当前 head 上执行新一轮 `pr_guardian review`。
- guardian 结论为 `APPROVE` 后走受控 `merge_pr`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 的首个实现切片补齐执行上下文追溯入口，不改变 `FR-0002` 已冻结的 contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#41` 的实现主事项（v0.1.0 首个 runtime/CLI 切片）。
- 阻塞：
  - 需要完成 `#44` 的 guardian 阻断收口后才能进入合并。

## 已验证项

- `PYTHONPATH=/Users/claw/code/worktrees/syvert/issue-41-runtime-local-single-process-executor-and-cli-skeleton python3 -m unittest tests.runtime.test_models tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_cli tests.governance.test_cli_smoke -v`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/governance_gate.py --mode ci --base-sha 3046b9a955b295c76665e2ed5e5dccf9bf58574b --head-ref HEAD`
- `python3 scripts/pr_guardian.py review 44 --post-review`（最近一次结论：`REQUEST_CHANGES`）
- `PYTHONPATH=/Users/claw/code/worktrees/syvert/issue-41-runtime-local-single-process-executor-and-cli-skeleton python3 -m unittest tests.runtime.test_cli.CliTests.test_loader_failure_uses_injected_task_id_factory -v`
- `PYTHONPATH=/Users/claw/code/worktrees/syvert/issue-41-runtime-local-single-process-executor-and-cli-skeleton python3 -m unittest tests.runtime.test_models tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_cli -v`

## 未决风险

- 若当前审查回合继续追加补件提交，PR 正文中的当前 head SHA 与验证信息必须同步刷新，否则 guardian 绑定会再次失配。
- 真实参考 adapter 尚未进入本 PR 范围；当前仅覆盖 runtime / CLI skeleton。

## 回滚方式

- 如需回滚，使用独立 revert PR 删除本文件。

## 最近一次 checkpoint 对应的 head SHA

- `83e4c7c4ecd8759d86255e57859a76537dda0fac`
- 上述 SHA 对应最近一次完成实现侧收口并通过局部测试的代码 checkpoint。
- 若当前审查回合仅追加 `exec-plan` / PR 正文等元数据补件提交，则实际用于 guardian 审查的当前 head SHA 以 PR `#44` 正文验证区块为准，并在每次补件后同步刷新。
