# CHORE-0140-fr-0015-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0140-fr-0015-formal-spec-closeout`
- Issue：`#194`
- item_type：`CHORE`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 状态：`active`
- active 收口事项：`CHORE-0140-fr-0015-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0015` formal spec 套件，冻结双参考适配器资源能力证据记录 carrier、`shared_status` 规则与 `v0.5.0` 最小能力词汇表。

## 范围

- 本次纳入：
  - `docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
  - `docs/exec-plans/FR-0015-dual-reference-resource-capability-evidence.md`
  - `docs/exec-plans/CHORE-0140-fr-0015-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - runtime / matcher / declaration 实现
  - `docs/releases/**`
  - `docs/sprints/**`
  - 根级治理文档与其他 FR 套件

## 当前停点

- `issue-194-fr-0015-formal-spec` 已作为 `#194` 的独立 spec worktree 建立。
- `FR-0015` formal spec 套件与 requirement container / Work Item exec-plan 已在当前分支首次落盘。
- 当前停点是补齐 formal spec 语义、通过门禁、生成首个 semantic checkpoint，并创建当前 spec PR。

## 下一步动作

- 运行 `spec_guard`、`docs_guard`、`workflow_guard` 与 `governance_gate`，修复 `FR-0015` 套件的一致性问题。
- 形成首个 semantic checkpoint 后回填 requirement container 与 closeout exec-plan 的 checkpoint SHA。
- 通过受控入口创建 spec PR，并把当前受审 PR、checks 与 checkpoint 真相同步回 exec-plan。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 把“哪些资源能力可以进入共享抽象”推进为 implementation-ready 的 formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0015` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 `FR-0015` 不先冻结证据基线，`FR-0013 / FR-0014` 会各自重新发明能力词汇。
  - 若双参考证据与能力命名未切开，单平台材料和技术字段会直接污染 Core 抽象。

## 已验证项

- 已核对 `#188`、`#191`、`#194` 对 `v0.5.0` 证据记录事项的目标、非目标与关闭条件描述。
- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md` 与 `spec_review.md` 的上位约束。
- 已核对 `FR-0010`、`FR-0012` 与当前 runtime / reference adapters / regression 基线，确认当前最小共享能力词汇应收敛为 `account`、`proxy`。

## 未决风险

- 若 `account` / `proxy` 之外的候选没有在当前 spec 中明确收口，下游 FR 仍可能把单平台字段或技术绑定字段带入 Core。
- 若 `proxy` 的批准语义写得过宽，后续事项可能误把它扩张成 provider taxonomy 或 richer network profile 抽象。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0015` formal spec 套件与当前 closeout exec-plan 的增量修改。

## checkpoint 记录方式

- semantic checkpoint：使用通过全部 formal-spec 门禁后的 commit SHA 作为唯一语义 checkpoint。
- review-sync follow-up：若后续只回填当前受审 PR、checks 或 checkpoint metadata，不把 metadata-only 修改伪装成新的语义 checkpoint。

## 最近一次 checkpoint 对应的 head SHA

- `待回填`
