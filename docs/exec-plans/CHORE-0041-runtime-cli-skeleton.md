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
- 最近一次实现 checkpoint 已推进到 `edb25f353b8237fd0c001a7d7c855b8377680df9`，已收口扩展 `TaskRequest` 顶层形状拒绝、CLI JSON 序列化 fail-closed 与对应回归测试。
- 当前受审 head 由 PR `#44` 正文验证区块绑定；若本轮仅追加 `exec-plan` / PR 正文等审查态元数据补件，不单独前推实现 checkpoint。
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

- 在仓库根目录执行：`PYTHONPATH=. python3 -m unittest tests.runtime.test_models tests.runtime.test_executor tests.runtime.test_runtime tests.runtime.test_cli tests.governance.test_cli_smoke -v`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/governance_gate.py --mode ci --base-sha 3046b9a955b295c76665e2ed5e5dccf9bf58574b --head-ref HEAD`
- `python3 scripts/pr_guardian.py review 44 --post-review`（最近一次结论：`REQUEST_CHANGES`）
- 上述命令已在实现 checkpoint `edb25f353b8237fd0c001a7d7c855b8377680df9` 对应工作树执行；当前受审 head 需在 PR `#44` 正文验证区块同步记录

## 未决风险

- 若当前审查回合继续追加补件提交，PR 正文中的当前 head SHA 与验证信息必须同步刷新，否则 guardian 绑定会再次失配。
- 真实参考 adapter 尚未进入本 PR 范围；当前仅覆盖 runtime / CLI skeleton。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `syvert/runtime.py`、`syvert/cli.py`、`tests/runtime/` 与本文件的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- 实现 checkpoint：`edb25f353b8237fd0c001a7d7c855b8377680df9`
- 当前受审 head：以 PR `#44` 正文验证区块记录的 head SHA 为准
- 前者用于恢复最近一次实现收口停点，后者用于绑定本轮 guardian / merge gate 的实际受审状态。
- 若当前审查回合继续追加 `exec-plan` / PR 正文等元数据补件提交，必须同步刷新“当前受审 head”与 PR 正文验证区块，避免审查绑定失配。
