# CHORE-0131-fr-0011-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0131-fr-0011-formal-spec-closeout`
- Issue：`#166`
- item_type：`CHORE`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：`docs/specs/FR-0011-task-bound-resource-tracing/`
- 关联 PR：`#169`
- 状态：`active`
- active 收口事项：`CHORE-0131-fr-0011-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0011` formal spec 套件，冻结资源状态跟踪、资源使用日志、task/resource 关联字段与最小事件时间线。

## 范围

- 本次纳入：
  - `docs/specs/FR-0011-task-bound-resource-tracing/`
  - `docs/exec-plans/FR-0011-task-bound-resource-tracing.md`
  - `docs/exec-plans/CHORE-0131-fr-0011-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `FR-0010` 的生命周期主接口与状态机
  - `FR-0012` 的 Adapter 注入 boundary
  - 共享 release/sprint 索引

## 当前停点

- `issue-166-fr-0011-formal-spec` 已作为 `#166` 的独立 spec worktree 建立。
- `FR-0011` formal spec 套件与 requirement container / Work Item exec-plan 已在当前分支首次落盘。
- 最新 formal spec 语义 checkpoint `8241217d65fe9dda57a783b55cbdec5d040f14de` 已生成，并已覆盖 guardian 指出的 `bundle_id` / `occurred_at` 语义补齐。
- spec PR `#169` 已创建并绑定当前分支。
- 当前停点是将最新语义 checkpoint 的验证链与 PR live head 对齐后继续进入 guardian / merge gate。

## 下一步动作

- 运行 `spec_guard`、`docs_guard`、`workflow_guard`，修复 tracing 套件与文档边界问题。
- 形成首个 formal spec checkpoint 后回填 exec-plan 的 checkpoint SHA 与验证结果。
- 通过受控入口创建 spec PR，并进入 review / guardian / merge gate。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 把“资源使用可以按任务追踪”推进为 implementation-ready 的 tracing contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0011` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 tracing truth 未冻结，后续实现与版本 gate 会各自长出不同审计口径。
  - lifecycle 主 contract 与 tracing contract 若未切开，会导致 `#164/#166` 相互覆盖。

## 已验证项

- 已核对 `#162`、`#165`、`#166` 对 `v0.4.0` 最小资源追踪闭环与本 Work Item 的目标、非目标与关闭条件描述。
- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`、`WORKFLOW.md` 与 `spec_review.md` 的上位约束。
- 已核对 formal spec 模板与近期 closeout 示例 `docs/exec-plans/CHORE-0126-fr-0009-formal-spec-closeout.md`。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `git commit -m 'docs(spec): 冻结 FR-0011 任务级资源追踪 formal spec'`
  - 结果：已生成初始 checkpoint `c330d9145746674447b2b894082e67083d91cc26`
- `git commit -m 'docs(spec): 对齐 FR-0011 tracing 字段语义'`
  - 结果：已生成中间语义 checkpoint `b19c63f3a025b327dc3485a36640236f096398fa`
- `git commit -m 'docs(spec): 收口 FR-0011 guardian 审查问题'`
  - 结果：已生成最新语义 checkpoint `8241217d65fe9dda57a783b55cbdec5d040f14de`

## 未决风险

- 若 tracing truth 不能证明 bundle 内多个资源属于同一 lease/task，则资源审计会退化为碎片化事件，无法回放占用过程。
- 若 tracing 被实现成 best-effort 日志，状态迁移成功但审计缺席的分叉会直接破坏 `v0.4.0` 的最小资源闭环。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0011` formal spec 套件与当前 closeout exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `8241217d65fe9dda57a783b55cbdec5d040f14de`
- review-sync 说明：本次 head 已吸纳 guardian 指出的语义补齐；后续若只追加 exec-plan / PR metadata，则不把 metadata-only follow-up 伪装成新的语义 checkpoint。
