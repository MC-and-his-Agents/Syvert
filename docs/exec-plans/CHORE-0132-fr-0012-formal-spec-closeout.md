# CHORE-0132-fr-0012-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0132-fr-0012-formal-spec-closeout`
- Issue：`#168`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0012-core-injected-resource-bundle/`
- 关联 PR：`#171`
- 状态：`active`
- active 收口事项：`CHORE-0132-fr-0012-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0012` formal spec 套件，冻结 Core 注入资源包、Adapter 禁止自行来源化执行资源，以及最终 release 仍由 Core 执行的边界 contract。

## 范围

- 本次纳入：
  - `docs/specs/FR-0012-core-injected-resource-bundle/`
  - `docs/exec-plans/FR-0012-core-injected-resource-bundle.md`
  - `docs/exec-plans/CHORE-0132-fr-0012-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `FR-0010` 的生命周期主接口与状态机
  - `FR-0011` 的 tracing / usage log schema
  - 共享 release/sprint 索引

## 当前停点

- `issue-168-fr-0012-formal-spec` 已作为 `#168` 的独立 spec worktree 建立。
- `FR-0012` formal spec 套件与 requirement container / Work Item exec-plan 已在当前分支首次落盘。
- 首个 formal spec 语义 checkpoint `d18c8eb40f17b89b773193e63d5bab1a81dd9203` 已生成，并已通过本地 `spec_guard`、`docs_guard` 与 `workflow_guard`。
- spec PR `#171` 已创建并绑定当前分支。
- 当前停点是等待 PR checks / guardian 基于当前 live head 继续收口。

## 下一步动作

- 运行 `spec_guard`、`docs_guard`、`workflow_guard`，修复注入 boundary 套件与文档边界问题。
- 形成首个 formal spec checkpoint 后回填 exec-plan 的 checkpoint SHA 与验证结果。
- 通过受控入口创建 spec PR，并进入 review / guardian / merge gate。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 把“Core 注入资源包、Adapter 不自行来源化资源”推进为 implementation-ready 的执行边界 contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0012` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 Core / Adapter 资源边界未冻结，reference adapter 改造会继续把资源语义私有化。
  - 若注入 boundary 与 `FR-0010` 的 bundle truth 不一致，后续生命周期与执行边界会分叉。

## 已验证项

- 已核对 `#162`、`#167`、`#168` 对 `v0.4.0` 资源注入边界与本 Work Item 的目标、非目标与关闭条件描述。
- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md` 与 `spec_review.md` 的上位约束。
- 已核对 formal spec 模板与近期 closeout 示例 `docs/exec-plans/CHORE-0126-fr-0009-formal-spec-closeout.md`。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `git commit -m 'docs(spec): 冻结 FR-0012 Core 注入资源边界 formal spec'`
  - 结果：已生成 checkpoint `d18c8eb40f17b89b773193e63d5bab1a81dd9203`

## 未决风险

- 若 Adapter 允许在注入 bundle 之外再额外来源化账号或代理，Core 将失去资源运行时语义的唯一真相源。
- 若 disposition hint 与最终 release 的责任边界未冻结，Adapter 可能越权直接改写资源状态并绕过 tracing truth。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0012` formal spec 套件与当前 closeout exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `d18c8eb40f17b89b773193e63d5bab1a81dd9203`
- review-sync 说明：后续若只追加 exec-plan / PR metadata，则不把 metadata-only follow-up 伪装成新的语义 checkpoint。
