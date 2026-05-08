# CHORE-0356 v0.9.0 provider compatibility spec 执行计划

## 关联信息

- item_key：`CHORE-0356-v0-9-provider-compatibility-spec`
- Issue：`#356`
- item_type：`CHORE`
- release：`v0.9.0`
- sprint：`2026-S22`
- 上位 Phase：`#354`
- 上位 FR：`#355`
- 关联 spec：`docs/specs/FR-0355-v0-9-real-provider-compatibility-evidence/`
- 关联 decision：`docs/decisions/ADR-CHORE-0356-v0-9-provider-compatibility-spec.md`
- active 收口事项：`CHORE-0356-v0-9-provider-compatibility-spec`
- 状态：`active`

## 目标

- 为 `v0.9.0` 建立真实 provider compatibility evidence formal spec。
- 明确后续 implementation / evidence Work Item 的进入条件和边界。
- 让 `FR-0351` 的 `provider_compatibility_sample` gate item 可以消费 `v0.9.0` evidence。

## 范围

- 本次纳入：
  - `docs/specs/FR-0355-v0-9-real-provider-compatibility-evidence/`
  - `docs/decisions/ADR-CHORE-0356-v0-9-provider-compatibility-spec.md`
  - `docs/exec-plans/CHORE-0356-v0-9-provider-compatibility-spec.md`
  - `docs/roadmap-v0-to-v1.md`
- 本次不纳入：
  - runtime、Adapter、Provider、tests、scripts 或 CI 代码
  - provider sample fixture / evidence artifact 实现
  - `v0.9.0` release index、tag 或 GitHub Release
  - provider selector、fallback、marketplace、上层应用或 Python package publish

## 当前停点

- GitHub Phase `#354`、FR `#355`、Work Item `#356` 已创建。
- 标准 worktree `issue-356-v0-9-0-provider-compatibility-formal-spec` 已创建。
- `FR-0355` formal spec suite、ADR、exec-plan 与 roadmap 引用正在落地。

## 下一步动作

- 完成本 spec PR 的本地门禁。
- 提交并推送分支。
- 通过受控入口创建 PR。
- GitHub checks 全部通过后运行 guardian。
- guardian 通过后执行受控合并，并创建 implementation / evidence Work Item。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.9.0` 收口建立 provider sample evidence 规约入口。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.9.0` provider compatibility evidence 的 formal spec 前置。
- 阻塞：如果本事项不收口，后续 implementation 无法可审查地判断 external provider sample 证明了什么、不证明什么。

## 已验证项

- `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`：通过
- `python3 scripts/docs_guard.py --mode ci`：通过
- `python3 scripts/workflow_guard.py --mode ci`：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`：通过
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`：通过，变更类别为 `docs, spec`
- `git diff --check origin/main..HEAD`：通过

## 未决风险

- 本事项只冻结 spec，不交付 provider sample evidence。
- 后续 implementation 若发现现有 validator 无法消费 external provider sample，必须用独立 implementation Work Item 修复，不得在 evidence 中绕过 contract。

## 回滚方式

- 使用独立 revert PR 撤销本事项新增的 `FR-0355` formal spec、ADR、exec-plan 与 roadmap 引用。

## 最近一次 checkpoint 对应的 head SHA

- `15f9d665702f14d8c9b808103084475a3c1a1a6c`
- 当前 PR head 由 guardian state / GitHub checks 绑定，不把本字段作为 merge gate 的 live head 替代来源。
