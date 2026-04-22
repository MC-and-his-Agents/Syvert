# CHORE-0140-fr-0015-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0140-fr-0015-formal-spec-closeout`
- Issue：`#194`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 关联 PR：
- 状态：`active`
- active 收口事项：`CHORE-0140-fr-0015-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0015` formal spec 套件，冻结双参考适配器资源能力证据记录 contract、研究边界与 `v0.5.0` 有限共享资源能力词汇表。

## 范围

- 本次纳入：
  - `docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
  - `docs/exec-plans/FR-0015-dual-reference-resource-capability-evidence.md`
  - `docs/exec-plans/CHORE-0140-fr-0015-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `FR-0013` 的 adapter 资源需求声明 contract
  - `FR-0014` 的 Core 资源能力匹配 contract
  - `#197` 的真实证据落盘实现

## 当前停点

- `issue-194-fr-0015-formal-spec` 已作为 `#194` 的独立 spec worktree 建立。
- `FR-0015` formal spec 套件与 requirement container / Work Item exec-plan 已在当前分支首次落盘。
- 当前 closeout 已把 `DualReferenceResourceCapabilityEvidenceRecord`、`shared_status` 枚举、有限词汇表与 research 边界写入 formal suite。
- 当前停点是先完成 formal suite 首次落盘，再运行 spec/docs/workflow/governance 四组 guard 并形成首个 semantic checkpoint。

## 下一步动作

- 运行 `spec_guard`、`docs_guard`、`workflow_guard` 与 `governance_gate`，修复 formal suite 与 exec-plan 的残余问题。
- 形成首个 formal spec checkpoint 后，回填 requirement container 与 closeout exec-plan 的 checkpoint / 验证真相。
- 通过受控入口创建 spec PR，并把 `#194` 与 `#191` 的 closeout / requirement truth 对齐到当前分支。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 把“新增资源能力抽象必须由双参考适配器证据解释”推进为 implementation-ready 的 formal evidence contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0015` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 `FR-0015` 不先冻结共享词汇表，`#192/#193` 会各自长出不同能力标识并污染 `v0.5.0` 的抽象边界。
  - 若共性语义、单平台特例与 rejected candidate 未被正式写清，后续 review 会退化为口头判断而不是 formal evidence。

## 已验证项

- 已核对 `#188`、`#191`、`#194` 对 `v0.5.0` 资源能力抽象收敛与本 Work Item 的目标、非目标与关闭条件描述。
- 已核对 `AGENTS.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md` 与 `spec_review.md` 的上位约束。
- 已核对 `FR-0010`、`FR-0011`、`FR-0012` 的 formal suite 与 requirement container / formal-spec-closeout exec-plan 模式，确保 `FR-0015` 套件形状与既有 closeout 基线一致。

## 未决风险

- 若 `managed_account / managed_proxy` 之外的词汇仍可被 `#192/#193` 任意消费，`v0.5.0` 会再次出现影子能力词汇表。
- 若单平台特例没有被正式记录为 `adapter_only` / `rejected`，后续事项很容易把 platform-private signal 误升格为共享抽象。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0015` formal spec 套件与当前 closeout exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `56d4860b21023fc2c0db71b6ba2e266f69911d9f`
