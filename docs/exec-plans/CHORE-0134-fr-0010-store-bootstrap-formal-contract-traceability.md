# CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability 执行计划

## 关联信息

- item_key：`CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability`
- Issue：`#177`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0010-minimal-resource-lifecycle/`
- 关联 PR：`#178`
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
- 本事项已把 `ResourceLifecycleSnapshot`、`seed_resources(records)`、snapshot `revision` compare-and-swap、same-value replay / no-op / conflict、默认本地入口 store-path，以及空 store 回落 canonical 空快照的语义补回 `spec.md`、`plan.md`、`data-model.md`、`contracts/README.md`、`risks.md` 与 requirement container。
- 最近三个语义提交继续扩大并收口 formal suite：
  - `ad78075`：把 store / bootstrap / revision / 默认本地入口 traceability 明确收回 FR-0010 主链路，而不是只留在附属文档或实现 PR。
  - `247ddd1`：重新收口范围、checkpoint 与 active exec-plan 对 formal traceability follow-up 的描述，避免 requirement container 与 active exec-plan 对同一事项给出不同停点。
  - `cc42965`：补齐 bootstrap 验证口径，明确“单批重复 `resource_id` 直接拒绝”“空 store 回落 canonical 空 snapshot”“implementation 阶段必须验证默认本地入口与 bootstrap/revision 语义”。
- 当前阻断不再是 formal spec 内容缺项，而是 guardian 指出 active exec-plan 仍停留在 `a90a90a` 对应的旧 checkpoint，错误声称“只剩 git / PR 收口”，与 `ad78075`、`247ddd1`、`cc42965` 之后的真实语义状态不一致。
- 本次修正的目标是把 active exec-plan 本身也推进到与当前 formal suite 同步的 checkpoint，避免 review 历史再次重复出现“formal 文档已前进、active exec-plan 仍落后”的系统性断层。
- 本事项仍只回写 FR-0010 formal artifact 与 active exec-plan，不改写 runtime / test 语义。
- 当前 worktree 在语义上已完成 traceability closeout；完成本次 exec-plan 对齐后，剩余工作才会真正收敛到 guard、review 与 merge gate。

## 下一步动作

- 运行 `spec_guard`、`docs_guard`、`workflow_guard`，确认 spec-only traceability follow-up 满足仓内文档与流程约束。
- 提交本次 active exec-plan checkpoint 对齐修正，并推送到 PR `#178`。
- 重新运行 guardian，确认 formal artifact 链已经不再存在 stale exec-plan / stale checkpoint 阻断。
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
- `sed -n '1,220p' docs/specs/FR-0010-minimal-resource-lifecycle/plan.md`
- `sed -n '1,220p' docs/specs/FR-0010-minimal-resource-lifecycle/contracts/README.md`
- `sed -n '1,220p' docs/specs/FR-0010-minimal-resource-lifecycle/risks.md`
- `sed -n '1,260p' docs/exec-plans/FR-0010-minimal-resource-lifecycle.md`
- `sed -n '1,260p' docs/exec-plans/CHORE-0134-fr-0010-store-bootstrap-formal-contract-traceability.md`
- `gh issue view 177 --json number,title,body,state,url`
  - 结果：已确认 `#177` 要求为 `#176` 补齐 `ResourceLifecycleSnapshot`、`seed_resources(records)`、`revision`、same-value replay / no-op / conflict 与默认本地 store-path 的 formal traceability
- `gh pr view 176 --json number,title,body,headRefName,baseRefName,state,url`
  - 结果：已确认 `#176` 为当前 implementation PR，当前缺口是 formal artifact 未显式覆盖 store / bootstrap surface
- `gh pr diff 176 --patch`
  - 结果：已核对 `ResourceLifecycleSnapshot`、`seed_resources(records)`、snapshot `revision` CAS、same-value replay / no-op / conflict、空 store 回落 canonical 空 snapshot、同批重复 `resource_id` 直接拒绝，以及 `SYVERT_RESOURCE_LIFECYCLE_STORE_FILE` 默认路径语义
- `git log --oneline --decorate -12`
  - 结果：已确认 `ad78075`、`247ddd1`、`cc42965` 是 `a90a90a` 之后的连续语义提交，当前 active exec-plan 需要显式吸收这些 checkpoint 变化
- `gh pr view 178 --json number,title,state,headRefName,baseRefName,mergeStateStatus,statusCheckRollup,url`
  - 结果：已确认 PR `#178` 当前 checks 为绿色，但 guardian 最新阻断仍是 active exec-plan stale checkpoint

## 未决风险

- 若本事项把 store / bootstrap 语义写成新的 public runtime surface，会反向扩张 `FR-0010` 范围并污染 `FR-0012` 边界。
- 若 formal artifact 只补字段名而不补 same-value replay / no-op / conflict 与 revision truth，`#176` 仍会在审查中被认定为缺少 canonical contract 依据。
- 若 active exec-plan 继续滞后于 formal suite 的真实语义 checkpoint，guardian 会重复把同一问题判定为 artifact-chain 不一致；因此本事项必须把“当前停点 / 下一步 / checkpoint head”与当前 HEAD 一并收口，而不是只更新 spec 文档正文。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 `FR-0010` formal artifact 与当前 active exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `cc429659f5ccf813a0bd893833afab7b7fc2584a`
