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
- 最近一次实现 checkpoint 已推进到 `65ffa67cc7659792e6db5303f8029a72c8dd6285`，已收口 CLI 参数解析 failure envelope 与 RFC3339 UTC 时间戳契约。
- 当前受审 head 由 PR `#44` 正文验证区块中的 `headRefOid` 绑定；本文件只维护当前实现 checkpoint 与审查追溯入口。
- 当前回合处于 guardian 阻断收口阶段，本文件与 sprint 索引同步维护实现回合的恢复入口。

## 下一步动作

- 继续收口 guardian 阻断项并同步 active 审查工件。
- 由受控审查链路基于当前受审 head 产出下一轮结论。
- 审查结论满足 merge gate 后走受控 `merge_pr`。

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
- `python3 scripts/pr_guardian.py review 44 --post-review`（审查结论以 PR `#44` review 记录与正文验证区块为准）
- 上述命令已在实现 checkpoint `65ffa67cc7659792e6db5303f8029a72c8dd6285` 对应工作树执行；当前受审 head 由 PR `#44` 正文验证区块同步记录

## 未决风险

- 若当前审查回合继续追加补件提交，PR 正文中的当前 head SHA 与验证信息必须同步刷新，否则 guardian 绑定会再次失配。
- 真实参考 adapter 尚未进入本 PR 范围；当前仅覆盖 runtime / CLI skeleton。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `syvert/runtime.py`、`syvert/cli.py`、`tests/runtime/` 与本文件的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- 实现 checkpoint：`65ffa67cc7659792e6db5303f8029a72c8dd6285`
- 当前受审 head：以 PR `#44` 正文验证区块中的 `headRefOid` 为准
- 前者用于恢复最近一次实现收口停点，后者用于绑定本轮 guardian / merge gate 的实际受审状态。
- 若当前审查回合继续追加 `exec-plan` / PR 正文等元数据补件提交，必须同步刷新“当前受审 head”与 PR 正文验证区块，避免审查绑定失配。
