# CHORE-0157-fr-0019-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0157-fr-0019-formal-spec-closeout`
- Issue：`#233`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0019-v0-6-operability-release-gate/`
- 关联 PR：`待创建`
- 状态：`active`
- active 收口事项：`CHORE-0157-fr-0019-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0019` formal spec 套件，冻结 `v0.6.0` 可运维发布门禁与回归矩阵，并把后续实现明确交给 `#234` release gate matrix implementation，再由 `#235` parent closeout 收口。

## 范围

- 本次纳入：
  - `docs/specs/FR-0019-v0-6-operability-release-gate/`
  - `docs/exec-plans/FR-0019-v0-6-operability-release-gate.md`
  - `docs/exec-plans/CHORE-0157-fr-0019-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `docs/releases/**`
  - `docs/sprints/**`
  - `FR-0007` 正文或既有版本 gate 语义改写
  - release closeout、tag、GitHub Release
  - 外部 SaaS 监控、生产验收、分布式压测

## 当前停点

- `issue-233-fr-0019-formal-spec` worktree 已用于 `#233` formal spec closeout。
- 当前回合只允许修改 `FR-0019` formal spec 套件与两个 exec-plan。
- 已完成初版 formal spec、plan、risks、data-model、contracts README 与两个 exec-plan 的落盘。
- 当前停点是运行三项 guard，并把实际验证命令与结果同步回本 exec-plan。

## 下一步动作

- 运行：`python3 scripts/spec_guard.py --mode ci --all`。
- 运行：`python3 scripts/docs_guard.py --mode ci`。
- 运行：`python3 scripts/workflow_guard.py --mode ci`。
- 若 guard 通过，准备进入 spec review / PR 创建链路；关联 PR 创建后将 `关联 PR` 从 `待创建` 更新为实际 PR。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 冻结 operability release gate 与回归矩阵，使 release gate matrix implementation 可以围绕 timeout / retry / concurrency、failure / log / metrics、HTTP submit / status / result、CLI / API same-path 建立同一套可复验门禁。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0019` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 `#233` 未完成 spec review，`#234` 不得进入 implementation。
  - 若 `#234` 未完成实现与门禁证据，`#235` 不得 parent closeout。
  - 若文档误把 `#233` 扩张成 release closeout / tag / GitHub Release，将违反当前 Work Item 边界。

## 已验证项

- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`docs/specs/README.md`。
- 已核对 formal spec 模板：`docs/specs/_template/spec.md`、`docs/specs/_template/plan.md`、`docs/specs/_template/risks.md`、`docs/specs/_template/data-model.md`。
- 已核对参考 spec：`FR-0007`、`FR-0008`、`FR-0009`、`FR-0015`。
- 已核对参考 exec-plan：`docs/exec-plans/CHORE-0138-fr-0013-formal-spec-closeout.md`。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。

## 未决风险

- 若 reviewer 要求 HTTP contract 固定更具体的 endpoint shape，需要确认是否仍属于 formal spec 层，避免提前绑定实现框架。
- 若后续 `#234` 发现现有 runtime 缺少可构造 timeout / concurrency case 的测试 seam，应在实现 PR 中补测试 seam，而不是回写本 Work Item 的实现代码。
- 若 GitHub 状态字段与仓内 exec-plan 不一致，应以 GitHub 为调度真相、repo 为语义真相分别收口，不能在 repo 内创建状态镜像。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0019` formal spec 套件与两个 exec-plan 的文档增量，不回退其他 Work Item、相邻 FR 或 runtime 变更。

## 最近一次 checkpoint 对应的 head SHA

- `待生成`
