# CHORE-0352 v1.0.0 Core stable release gate spec 执行计划

## 关联信息

- item_key：`CHORE-0352-v1-core-stable-release-gate-spec`
- Issue：`#352`
- item_type：`CHORE`
- release：`v1.0.0`
- sprint：`2026-S22`
- 上位 Phase：`#350`
- 上位 FR：`#351`
- 关联 spec：`docs/specs/FR-0351-v1-core-stable-release-gate/`
- 关联 decision：`docs/decisions/ADR-CHORE-0352-v1-core-stable-release-gate-spec.md`
- active 收口事项：`CHORE-0352-v1-core-stable-release-gate-spec`
- 状态：`active`

## 目标

- 为 `v1.0.0` Core stable 建立正式 release gate checklist。
- 让后续 `v0.9.0` 真实 provider 样本可以明确映射到 `v1.0.0` gate。
- 明确上层应用、provider selector / fallback / marketplace 与 Python package publish 不属于 `v1.0.0` 默认完成条件。

## 范围

- 本次纳入：
  - `docs/specs/FR-0351-v1-core-stable-release-gate/`
  - `docs/decisions/ADR-CHORE-0352-v1-core-stable-release-gate-spec.md`
  - `docs/exec-plans/CHORE-0352-v1-core-stable-release-gate-spec.md`
  - `docs/roadmap-v0-to-v1.md`
- 本次不纳入：
  - `docs/process/version-management.md` governance 文档
  - runtime、Adapter、Provider、tests、scripts 或 CI 代码
  - `v0.9.0` provider sample implementation
  - `v1.0.0` release closeout
  - Python packaging implementation

## 当前停点

- GitHub Phase `#350`、FR `#351`、Work Item `#352` 已创建。
- 标准 worktree `issue-352-v1-0-0-release-gate-formal-spec` 已创建。
- `FR-0351` formal spec suite、ADR、exec-plan 与 roadmap 引用已落地。
- 本地 spec / docs / workflow / governance / scope / whitespace 门禁已通过。
- PR `#353` 已创建，GitHub checks 是当前 head 的 live verification entry。

## 下一步动作

- 更新 PR 后等待 GitHub checks。
- GitHub checks 全部通过后运行 guardian merge gate。
- guardian 通过后执行受控合并与 closeout。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.0.0` 发布前置建立 Core stable release gate，让 `v0.9.0` 的真实 provider sample 工作有明确消费目标。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.9.0` 前置 gate formalization。
- 阻塞：如果本事项不收口，`v0.9.0` 完成后仍缺少可审查的 `v1.0.0` Core stable 判定标准。

## 已验证项

- 本地验证入口：
  - `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`：通过
  - `python3 scripts/docs_guard.py --mode ci`：通过
  - `python3 scripts/workflow_guard.py --mode ci`：通过
  - `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`：通过
  - `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`：通过，变更类别为 `docs, spec`
  - `git diff --check origin/main..HEAD`：通过
- GitHub verification entry：
  - PR `#353` GitHub Checks 是当前 PR head 的 live evidence。
  - guardian review packet 以 PR `#353` current head 为准；本文件不替代 guardian state 或 GitHub checks。

## 未决风险

- 本事项只冻结 gate，不交付 `v0.9.0` provider sample。
- 若后续 `v0.9.0` provider sample 发现 gate 缺项，必须通过独立 spec follow-up 修改 `FR-0351`。

## 回滚方式

- 使用独立 revert PR 撤销本事项新增的 `FR-0351` formal spec、ADR、exec-plan 与 roadmap 引用。

## 最近一次 checkpoint 对应的 head SHA

- `183a0d16a92a4396543993df8fb0537505a63e76`
- 当前 PR head 由 guardian state / GitHub checks 绑定，不把本字段作为 merge gate 的 live head 替代来源。
