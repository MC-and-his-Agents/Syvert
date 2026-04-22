# CHORE-0146-fr-0015-evidence-closeout-rerun 执行计划

## 关联信息

- item_key：`CHORE-0146-fr-0015-evidence-closeout-rerun`
- Issue：`#211`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 关联 PR：`TBD`
- 状态：`active`
- active 收口事项：`CHORE-0146-fr-0015-evidence-closeout-rerun`

## 目标

- 在 `main@b1f918885b751f4278cf2216204cbb90c0e57b2d` 的干净主干上，重新落地 `FR-0015` machine-readable dual-reference resource capability evidence baseline。
- 复用 `#197 / PR #204` 已收敛的实现内容，但在新的合法 Work Item / 分支 / PR 上重新完成 review、guardian 与 merge gate 收口。
- 让 `#195/#196` 后续只能从单一代码 registry 读取 `approved` capability ids 与 traceable `evidence_refs`，不再复制 `account`、`proxy` 或 evidence 字符串。

## 范围

- 本次纳入：
  - 新增 `syvert/resource_capability_evidence.py` 作为 `FR-0015` evidence baseline 的唯一代码入口
  - 新增 `tests/runtime/test_resource_capability_evidence.py` 复验 registry、runtime 事实与 formal research traceability
  - 新增 `docs/exec-plans/artifacts/CHORE-0146-fr-0015-resource-capability-evidence-baseline.md` 作为人类可审 artifact
  - 更新 `docs/exec-plans/FR-0015-dual-reference-resource-capability-evidence.md`，追加 `#211` rerun round 的追溯入口
- 本次不纳入：
  - 修改 `docs/specs/FR-0015-dual-reference-resource-capability-evidence/` formal spec 语义
  - 修改 `syvert/runtime.py`、reference adapter 或 `syvert/version_gate.py` 的运行语义
  - 修改 `#195 / FR-0013`、`#196 / FR-0014` 的实现
  - 修改 release / sprint 索引

## 当前停点

- `#197 / PR #204` 曾把同一实现合入 `main`，merge commit 为 `a8b6ffc87b41afae5d4d9c4e95de74791e521b5b`。
- 由于该次合入未等待 latest guardian 对当前受审 head 给出明确 `APPROVE`，已由 `#209 / PR #210` 回退，回退后 `main` 基线为 `b1f918885b751f4278cf2216204cbb90c0e57b2d`。
- 当前 rerun worktree 为 `/Users/mc/code/worktrees/syvert/issue-211-fr-0015`，目标是在不改写 formal spec truth 的前提下，把已验证实现重新接回受控 merge 路径。

## 下一步动作

- 完成 code / tests / artifact / requirement-container traceability 迁入。
- 执行固定本地验证命令与 PR scope / governance 门禁。
- 创建新的 implementation PR，并把 PR 号回写到本 exec-plan。
- 等待 GitHub checks 全绿与 latest guardian `APPROVE`，确认 `safe_to_merge=true` 且 review / merge 绑定同一 head 后，再执行受控 squash merge。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 恢复 `FR-0015` 共享资源能力证据基线的可信实现入口，使后续 `FR-0013/FR-0014` 能直接消费同一份批准能力词汇与证据引用。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0015` evidence implementation closeout 的合法 rerun Work Item。
- 阻塞：
  - 在本回合重新合入前，`main` 只有 formal registry truth，没有 machine-readable evidence registry truth。
  - 若再次在未获得 latest guardian `APPROVE` 前合入，会重复同类流程违背。

## 已验证项

- `python3 scripts/create_worktree.py --issue 211 --class implementation`
  - 结果：已创建当前 worktree `/Users/mc/code/worktrees/syvert/issue-211-fr-0015`
  - base SHA：`b1f918885b751f4278cf2216204cbb90c0e57b2d`

## 未决风险

- 若当前主干事实已偏离 `#197` 收敛实现依赖的 runtime / adapter 证据面，迁入后的 traceability tests 可能暴露 formal spec 与实现真相漂移。
- 若 artifact 与代码 registry 不再一一对应，后续 `#195/#196` 可能再次复制能力名或 evidence ref 字符串，破坏单一事实源。
- 若 guardian 对当前受审 head 提出重复类阻断，必须按系统性根因修复，而不是只做单点补丁。

## 回滚方式

- 若本 rerun round 发现实现与 formal spec 基线冲突，使用独立 Work Item + revert PR 回退当前 implementation PR；不得改写 `#197/#204` 或 `#209/#210` 的历史回合真相。

## 最近一次 checkpoint 对应的 head SHA

- `TBD`
