# CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability 执行计划

## 关联信息

- item_key：`CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability`
- Issue：`#177`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0010-minimal-resource-lifecycle/`
- 关联 PR：
- 状态：`active`
- active 收口事项：`CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability`

## 目标

- 为 `FR-0010` 补齐本地 snapshot store / bootstrap surface 的 formal contract traceability，使 implementation PR `#176` 可以直接引用 canonical spec artifact，而不需要在实现 PR 中补写 requirement。

## 范围

- 本次纳入：
  - `docs/specs/FR-0010-minimal-resource-lifecycle/spec.md`
  - `docs/specs/FR-0010-minimal-resource-lifecycle/plan.md`
  - `docs/specs/FR-0010-minimal-resource-lifecycle/data-model.md`
  - `docs/specs/FR-0010-minimal-resource-lifecycle/contracts/README.md`
  - `docs/specs/FR-0010-minimal-resource-lifecycle/risks.md`
  - `docs/exec-plans/FR-0010-minimal-resource-lifecycle.md`
  - `docs/exec-plans/CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `FR-0011` 的 tracing schema
  - `FR-0012` 的 Adapter 注入 boundary

## 当前停点

- `FR-0010` formal spec 主 contract 已由 PR `#170` 合入主干，资源类型、bundle / lease carrier、状态迁移与 `acquire / release` 语义已经冻结。
- implementation PR `#176` 已新增本地 snapshot store、`ResourceLifecycleSnapshot`、`seed_resources(records)`、snapshot `revision` 与 same-value replay / no-op / conflict 行为。
- 当前阻断不在运行时代码，而在 formal artifact 仍缺少 store / bootstrap traceability，导致 `#176` 的实现 surface 缺少可引用的 canonical contract 依据。
- 当前补丁同时回写 `spec.md` / `plan.md`，把 store / bootstrap surface 提升回 FR 主文档与实施计划，避免 formal suite 内部出现“核心文档无追踪、附属文档单独冻结”的断层。
- 当前补丁也同步刷新 `risks.md` 与 requirement container，确保新增 snapshot / bootstrap / revision / 默认本地入口语义进入 formal suite 的最小审查输入。
- 本事项只回写 FR-0010 formal artifact 与 active exec-plan，不改写 runtime / test 语义。
- 当前 worktree 已补齐 store / bootstrap traceability，并已通过 `spec_guard`、`docs_guard`、`workflow_guard`；下一步只剩由主线程执行 git / PR 收口。

## 下一步动作

- 运行 `spec_guard`、`docs_guard`、`workflow_guard`，确认 spec-only traceability follow-up 满足仓内文档与流程约束。
- 由主线程基于当前 worktree 创建独立 spec PR，优先把 `#177` 合入主干。
- `#177` 合入后，回到 implementation PR `#176` 刷新 guardian / merge gate，并在审查回复中引用本次补齐的 formal artifact。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 把 `FR-0010` 的 host-side durable snapshot / bootstrap 边界补齐到 implementation-ready，可直接支撑本地 store 与 bootstrap runtime 收口。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0010` 的 spec-only traceability follow-up，负责把已进入实现面的 store / bootstrap 语义收回到 canonical formal artifact。
- 阻塞：
  - 若 `ResourceLifecycleSnapshot`、`seed_resources(records)`、`revision` 与默认 store-path 仍只存在于实现 PR，guardian 会继续把 `#176` 判定为缺 formal traceability。

## 已验证项

- `sed -n '1,260p' docs/specs/FR-0010-minimal-resource-lifecycle/spec.md`
- `sed -n '1,220p' docs/specs/FR-0010-minimal-resource-lifecycle/data-model.md`
- `sed -n '1,220p' docs/specs/FR-0010-minimal-resource-lifecycle/contracts/README.md`
- `sed -n '1,260p' docs/exec-plans/FR-0010-minimal-resource-lifecycle.md`
- `sed -n '1,260p' docs/exec-plans/CHORE-0130-fr-0010-formal-spec-closeout.md`
- `gh issue view 177 --json number,title,body,state,url`
  - 结果：已确认 `#177` 要求为 `#176` 补齐 `ResourceLifecycleSnapshot`、`seed_resources(records)`、`revision`、same-value replay / no-op / conflict 与默认本地 store-path 的 formal traceability
- `gh pr view 176 --json number,title,body,headRefName,baseRefName,state,url`
  - 结果：已确认 `#176` 为当前 implementation PR，当前缺口是 formal artifact 未显式覆盖 store / bootstrap surface
- `gh pr diff 176 --patch`
  - 结果：已核对 `ResourceLifecycleSnapshot`、`seed_resources(records)`、snapshot `revision` CAS、same-value replay / no-op / conflict 与 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE` 默认路径语义
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过

## 未决风险

- 若本事项把 store / bootstrap 语义写成新的 public runtime surface，会反向扩张 `FR-0010` 范围并污染 `FR-0012` 边界。
- 若 formal artifact 只补字段名而不补 same-value replay / no-op / conflict 与 revision truth，`#176` 仍会在审查中被认定为缺少 canonical contract 依据。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `FR-0010` formal artifact 与当前 active exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `a90a90af017c9f2b9db611319d8c8f0fb4f07c70`
