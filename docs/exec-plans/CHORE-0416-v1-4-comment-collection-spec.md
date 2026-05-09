# CHORE-0416 v1.4 comment collection spec 执行计划

## 关联信息

- item_key：`CHORE-0416-v1-4-comment-collection-spec`
- Issue：`#416`
- item_type：`CHORE`
- release：`v1.4.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#404`
- 关联 spec：`docs/specs/FR-0404-comment-collection-contract/spec.md`
- 关联 decision：`docs/decisions/ADR-CHORE-0416-comment-collection-operation-name.md`
- 关联 PR：`#427`
- 状态：`active`

## 目标

- 完成 `#404` 的 Batch 0 与 Batch 1。
- 交付脱敏 comment fixture/error inventory、formal spec suite、`v1.4.0` release planning index 与 `2026-S25` sprint update。
- 只冻结 `comment_collection` contract，不交付 runtime carrier、consumer migration、fake/reference tests implementation、release closeout 或 raw fixture payload files。

## 范围

- 本次纳入：
  - `docs/exec-plans/artifacts/CHORE-0416-v1-4-comment-collection-fixture-inventory.md`
  - `docs/exec-plans/CHORE-0416-v1-4-comment-collection-spec.md`
  - `docs/decisions/ADR-CHORE-0416-comment-collection-operation-name.md`
  - `docs/roadmap-v1-to-v2.md`
  - `docs/specs/FR-0404-comment-collection-contract/spec.md`
  - `docs/specs/FR-0404-comment-collection-contract/plan.md`
  - `docs/specs/FR-0404-comment-collection-contract/data-model.md`
  - `docs/specs/FR-0404-comment-collection-contract/contracts/README.md`
  - `docs/specs/FR-0404-comment-collection-contract/risks.md`
  - `docs/releases/v1.4.0.md`
  - `docs/sprints/2026-S25.md`
- 本次不纳入：
  - `syvert/**` runtime implementation
  - `tests/**` implementation or fixture payloads
  - `#405` Work Item creation or execution
  - release closeout, annotated tag, GitHub Release, published truth carrier
  - raw fixture payload files and any external source name/path mapping

## 当前停点

- Phase `#381`：open，作为 Phase container。
- FR `#404`：open，已显式绑定 `v1.4.0 / 2026-S25`。
- Work Item `#416`：open，唯一进入当前 spec workspace 的事项。
- Workspace key：`issue-416-404-v1-4-0-comment-collection-spec`
- Branch：`issue-416-404-v1-4-0-comment-collection-spec`
- 主仓 baseline：`04314d6de9c008cccf5719e982fc7dde67652f83`
- 当前变更：Batch 0 artifact、`FR-0404` formal spec suite、`v1.4.0` release planning index 与 `2026-S25` sprint update 已写入，当前处于 spec review / guardian 收口阶段。

## 下一步动作

- 收敛剩余 guardian finding，并重新运行 checks / guardian。
- 通过 merge gate 后合并 `#427`。
- 合并后从主干进入 `#417` runtime carrier；不得在本 PR 中提前实施 runtime、consumer 或 evidence。

## 当前 checkpoint 推进的 release 目标

- 为 `v1.4.0` 明确首个 comment-collection contract batch 的 planning truth。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`#404` formal spec carrier。
- 阻塞：如 `#427` 的 `spec review` / guardian 未通过，不得进入 `#417` runtime carrier。

## 已验证项

- `#381/#404/#416` GitHub truth 已对齐到本批次执行入口。
- `#404` 当前已显式绑定 `release=v1.4.0`、`sprint=2026-S25`。
- 独立 worktree 与 issue-scoped branch 已创建。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。
- 脱敏搜索
  - 结果：新增文档未包含外部项目名或本地路径。
- PR guardian refresh review
  - 结果：曾阻塞于 operation 命名、request continuation 字段映射与 comment ref 绑定歧义。
  - 处理：已按当前 canonical taxonomy candidate 统一 public operation 为 `comment_collection`，并通过 `ADR-CHORE-0416-comment-collection-operation-name` 与 roadmap 写回明确其取代 `comment_list_by_content` 作为 `#404` slice 的 public operation。
  - 处理：已冻结 result `next_continuation` -> request `page_continuation` 映射，并把 reply/hierarchy/cursor 绑定固定到 `NormalizedCommentItem.canonical_ref`。
  - 最新处理：已修正 placeholder comment identity 规则，`source_id` 继续作为 `FR-0403` item identity 基线；deleted/invisible/unavailable placeholder 缺少平台稳定 id 时，不得伪造平台原生 id，必须通过 public placeholder namespace 与独立稳定 placeholder marker 派生稳定 `source_id` 与 `canonical_ref`。
- `#427` 已创建，当前 head 绑定本事项的 review round。

## 未决风险

- 若 comment contract 直接复用 `#403` content item shape，会把评论层级、visibility 与 reply cursor 继续留在平台私有语义里。
- 若 formal spec 把 deleted/invisible 设计成 collection-level error，而不是 item-level visibility，将导致后续 runtime 难以表达混合页面。
- 若 `v1.4.0` release index 被误写成 published truth，`version_guard` 会把 planning 文档误判成发布事实。

## 回滚方式

- 使用独立 revert PR 撤销本 Work Item 新增的 spec/docs/artifact 增量。
- 保留 `#381/#404/#416` truth，并在 FR 下重新收敛下一步 Work Item。

## 最近一次 checkpoint 对应的 head SHA

- Initial branch checkpoint：`04314d6de9c008cccf5719e982fc7dde67652f83`
- Current live PR head is governed by PR `headRefOid` and guardian merge gate after PR creation.
