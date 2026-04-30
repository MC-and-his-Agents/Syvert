# CHORE-0298-fr-0027-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0298-fr-0027-formal-spec-closeout`
- Issue：`#299`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0298-fr-0027-formal-spec-closeout`
- 状态：`active`

## 目标

- 建立并收口 `FR-0027` formal spec 套件，冻结多 profile declaration carrier、matcher `one-of` 语义与 profile evidence 边界，为 `#300/#301/#302` 提供 governing artifact。

## 范围

- 本次纳入：
  - `docs/specs/FR-0027-multi-profile-resource-requirement-contract/`
  - `docs/exec-plans/FR-0027-multi-profile-resource-requirement-contract.md`
  - `docs/exec-plans/CHORE-0298-fr-0027-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - runtime matcher / evidence artifact / reference adapter 声明实现
  - `docs/releases/**`
  - `docs/sprints/**`
  - 其它 formal spec 套件

## 当前停点

- `issue-299-fr-0027-formal-spec` 已作为 `#299` 的独立 spec worktree 建立，基线为 `3410c212c3bc2a233892bcb5cf014fe90201fa19`。
- 已核对 `#294` 与 `#299-#303` 的目标、非目标与依赖关系。
- 当前 formal spec 回合采用“`FR-0027` 新主套件承接 `v0.8.0` truth，`FR-0013/14/15` 保留 `v0.5.0` 历史语义”的落盘策略，以满足现有 formal spec scope guard。

## 下一步动作

- 完成 `FR-0027` formal spec 套件与 requirement container。
- 运行 `spec_guard`、`docs_guard`、`workflow_guard` 与 `governance_gate`。
- 创建 spec PR，并把 review / guardian / merge gate 真相同步回 exec-plan。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 multi-profile resource requirement、matcher `one-of` 与 profile evidence 边界推进为 implementation-ready formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0027` 的 formal spec closeout Work Item。
- 阻塞：
  - `#300`、`#301`、`#302` 都依赖本 spec 合入主干。
  - 若本 spec 不先冻结，evidence、runtime 与 reference adapter migration 会继续绑在旧的单声明模型上。

## 已验证项

- `python3 scripts/create_worktree.py --issue 299 --class spec`
  - 结果：通过，创建 worktree `issue-299-fr-0027-formal-spec`
- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md`、`docs/AGENTS.md`、`docs/process/delivery-funnel.md` 与 `spec_review.md` 的上位约束。
- 已核对 `FR-0013`、`FR-0014`、`FR-0015` 当前 `v0.5.0` 单声明基线与 `#294` 的 `v0.8.0` 目标差异。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-299-fr-0027-formal-spec`
  - 结果：通过

## 未决风险

- 若 `FR-0027` 没有明确写清 supersede 边界，后续事项可能继续并行消费旧 `FR-0013/14/15` 的单声明 truth。
- 若多 profile 被写成优先级 / fallback 语义，runtime 与 adapter migration 会越过 `#294` 明确不在范围的边界。

## 回滚方式

- 使用独立 revert PR 撤销 `docs/specs/FR-0027-multi-profile-resource-requirement-contract/` 与本 exec-plan / requirement container 的增量修改。
- 若需要改变 `FR-0027` 范围，必须先更新 `#294`，不得在后续实现 PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- `3410c212c3bc2a233892bcb5cf014fe90201fa19`
- worktree 创建基线：`3410c212c3bc2a233892bcb5cf014fe90201fa19`
