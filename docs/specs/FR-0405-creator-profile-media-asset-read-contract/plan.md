# FR-0405 Creator profile and media asset read contract 实施计划

## 关联信息

- item_key：`FR-0405-creator-profile-media-asset-read-contract`
- Issue：`#405`
- item_type：`FR`
- release：`v1.5.0`
- sprint：`2026-S25`
- 关联 exec-plan：`docs/exec-plans/CHORE-0421-v1-5-creator-profile-media-asset-spec.md`
- spec review：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec-review.md`

## 实施目标

- 本次实施只交付 `FR-0405` 的 Batch 0 inventory 与 Batch 1 formal spec suite。
- 后续 Work Item 才允许更新 canonical taxonomy / admission inputs、实现 creator profile runtime carrier、media asset fetch runtime carrier、consumer migration、fake/reference evidence 与 release closeout。

## 分阶段拆分

- 阶段 1：`#421` 冻结 Batch 0 fixture/error inventory，形成 reviewable acquisition matrix 与公共错误分类。
- 阶段 2：`#421` 冻结 `FR-0405` formal spec、data model、contract README 与 risks。
- 阶段 3：`#422` 将 `creator_profile_by_id` 所需 taxonomy / Adapter requirement / Provider offer / compatibility decision 输入域从 proposed-only 推进到 approved execution slice，并实现 creator profile runtime carrier。
- 阶段 4：`#423` 将 `media_asset_fetch_by_ref` 所需 taxonomy / Adapter requirement / Provider offer / compatibility decision 输入域从 proposed-only 推进到 approved execution slice，并实现 media asset fetch runtime carrier。
- 阶段 5：`#424` 迁移 TaskRecord / result query consumer；compatibility decision 只迁移 admission input validation，不消费 result carriers。
- 阶段 6：`#425` 补齐 fake/reference evidence 与 two-reference or equivalent proof。
- 阶段 7：`#426` 完成 `v1.5.0` release-slice closeout truth，并评估 Phase `#381` close conditions。

## 实现约束

- 不允许触碰 runtime、tests implementation、raw fixture payload files。
- 不允许把 comment hierarchy、reply cursor、comment visibility semantics 混入 `FR-0405`。
- 不允许把 media upload、content publish、asset library、media storage lifecycle 或 content library product behavior 混入 Core contract。
- 不允许在 repository 或 GitHub truth 中出现外部项目名或本地路径。
- 不允许把 `v1.5.0` 写成整个 Phase 3 的 release 绑定。
- 不允许修改 `content_detail_by_url` baseline 或 `#403` collection envelope；`#404` shared runtime/consumer conflict risk 由后续 runtime Work Item 在进入实现前单独评估。

## 测试与验证策略

- 单元测试：本 Work Item 不新增 runtime 单元测试。
- 集成/契约测试：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `python3 scripts/version_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-421-405-v1-5-0-creator-profile-media-asset-spec`
  - `git diff --check`
- 手动验证：
  - 核对 `#381/#405/#421` truth 与 `v1.5.0` / `2026-S25` planning truth 一致。
  - 搜索变更内容，确认不含外部项目名或本地路径。
  - 用 `spec_review.md` rubric 做 formal spec review，并把结论记录到 `docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec-review.md`。

## TDD 范围

- 先写测试的模块：不适用，本 Work Item 只交付 formal spec 与 planning truth。
- 暂不纳入 TDD 的模块与理由：runtime carrier、consumer migration 与 evidence replay 均由后续 Work Item 承接。

## 并行 / 串行关系

- 可并行项：
  - `v1.5.0` release planning index
  - `2026-S25` sprint index update
  - Batch 0 inventory artifact
  - `#404` 独立会话中的 spec/runtime 工作，前提是本 Work Item 不触碰 runtime/consumer 实现路径
- 串行依赖项：
  - spec suite 需要先消费 Batch 0 inventory 中的场景矩阵与错误分类。
  - `#422/#423` runtime carrier 必须等待本 Work Item 合入、canonical taxonomy/admission extension plan 明确，以及 `#404` shared runtime conflict-risk clearance。
  - `#424` consumer migration 必须等待 `#422/#423` 合入。
  - `#425` evidence 必须等待 `#424` 合入。
  - `#426` closeout 必须等待 `#425` 合入。
- 阻塞项：
  - 若 `spec review` 未通过，不得进入 runtime implementation Work Item。

## 进入实现前条件

- [x] `spec review` 已通过：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec-review.md`
- [x] 关键风险已记录并有缓解策略：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/risks.md`
- [x] `#421` spec-freeze 关键依赖可用：Batch 0 inventory 与 formal spec suite 已齐备
- [x] `creator_profile` / `media_asset_fetch` 的 taxonomy lifecycle 与 `FR-0024/FR-0025/FR-0026` admission 输入域扩展路径已明确为 `#422/#423`
- [ ] `#404` shared runtime/consumer conflict-risk clearance 已记录，或 `#404` 相关 shared paths 已完成稳定 closeout

本清单不表示 `#421` 交付 runtime implementation-ready。`#422/#423` 只能在未完成项满足后进入 runtime execution。
