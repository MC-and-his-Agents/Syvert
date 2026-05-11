# CHORE-0426 v1.5 creator media closeout

## 关联信息

- item_key：`CHORE-0426-v1-5-creator-media-closeout`
- Issue：`#426`
- item_type：`CHORE`
- release：`v1.5.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#405`
- 关联 spec：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/`
- 关联 PR：待创建
- 状态：`active`
- active 收口事项：`CHORE-0426-v1-5-creator-media-closeout`

## 目标

- Work Item：`#426`
- Parent FR：`#405`
- Scope：消费 `#421/#422/#423/#424/#425` 的 merged truth、验证结果与审计证据，完成 `#405` closeout、`v1.5.0` 发布锚点（tag + GitHub Release）与 release/sprint 索引回写。
- Out of scope：新增 runtime 行为、formal spec 语义扩展、Phase `#381` 自动关闭推断。

## 改动记录

- 基于 `origin/main@ddebe39040be0c7a9374a923f15004e3880a45bc` 更新 `v1.5.0` release index、`2026-S25` sprint index 和 `#405` closeout evidence。
- 统一记录 `#421-#425` 的 PR / merge commit / validation inputs，并将 `#442` 的受控 merge provenance 纳入 closeout 事实链。
- 保留 `#439/#440/#441` 的 manual merge provenance 事实，不将其改写为标准 `merge-if-safe` provenance；同时记录 `#442` 已走 guardian approve + `merge-if-safe`。
- 在发布完成后回写 annotated tag object、tag target、GitHub Release URL、published timestamp。

## 验证记录

- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `git diff --check`
- 发布锚点验证：
  - `git rev-parse v1.5.0^{tag}`
  - `git rev-parse v1.5.0^{}`
  - `gh release view v1.5.0 --json tagName,url,publishedAt,targetCommitish`

## Review finding 处理记录

- 历史 finding：`#439/#440/#441` 未通过标准 `merge-if-safe`。
- 处理：以 post-merge audit artifact 固定 provenance 与回滚门槛，并在 `#442` 上补齐标准 guardian + merge-if-safe 路径证明。

## 未决风险

- Phase `#381` close conditions 需独立评估，不应从 `v1.5.0` 发布自动推导。
- 若 closeout PR 被 guardian/checks 阻断，`#405/#426` 不得关闭，release 索引需维持 pending 状态。

## 回滚方式

- closeout truth 错误：使用独立 docs PR 与 GitHub issue/release metadata 修正，不回滚 `#421-#425` 已合入实现。
- 若发布后复现 runtime/contract drift：创建独立 remediation/revert Work Item，按回滚门槛处理，不在 closeout PR 混入代码修复。

## 最近一次 checkpoint 对应的 head SHA

- `ddebe39040be0c7a9374a923f15004e3880a45bc`
