# FR-0403 Read-side collection result and cursor contract 实施计划

## 关联信息

- item_key：`FR-0403-read-side-collection-result-cursor-contract`
- Issue：`#403`
- item_type：`FR`
- release：`v1.3.0`
- sprint：`2026-S25`
- 关联 exec-plan：`docs/exec-plans/CHORE-0406-v1-3-read-side-collection-spec.md`

## 实施目标

- 本次实施只交付 `FR-0403` 的 Batch 0 inventory 与 Batch 1 formal spec suite。
- 后续 Work Item 才允许实现 runtime carrier、consumer migration、fake/reference evidence 与 release closeout。

## 分阶段拆分

- 阶段 1：`#406` 冻结 Batch 0 fixture/error inventory，形成 reviewable acquisition matrix 与公共错误分类。
- 阶段 2：`#406` 冻结 `FR-0403` formal spec、data model、contract README 与 risks。
- 阶段 3：后续 Work Item 实现 collection runtime carrier。
- 阶段 4：后续 Work Item 迁移 TaskRecord / result query / compatibility decision 等 consumer。
- 阶段 5：后续 Work Item 补齐 fake/reference evidence、spec review closeout 与 `v1.3.0` release closeout。

## 实现约束

- 不允许触碰 runtime、tests implementation、raw fixture payload files。
- 不允许把 comment hierarchy、creator profile、media download/no-download boundary 混入 `FR-0403`。
- 不允许在 repository 或 GitHub truth 中出现外部项目名或本地路径。
- 不允许把 `v1.3.0` 写成整个 Phase 3 的 release 绑定。
- 不允许修改 `content_detail_by_url` baseline 或 Phase 2 resource governance 语义。

## 测试与验证策略

- 单元测试：本 Work Item 不新增 runtime 单元测试。
- 集成/契约测试：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `python3 scripts/version_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-406-403-v1-3-0-read-side-collection-spec`
  - `git diff --check`
- 手动验证：
  - 核对 `#381/#403/#406` truth 与 `v1.3.0` / `2026-S25` planning truth 一致。
  - 搜索变更内容，确认不含外部项目名或本地路径。
  - 用 `spec_review.md` rubric 做 formal spec review。

## TDD 范围

- 先写测试的模块：不适用，本 Work Item 只交付 formal spec 与 planning truth。
- 暂不纳入 TDD 的模块与理由：runtime carrier、consumer migration 与 evidence replay 均由后续 Work Item 承接。

## 并行 / 串行关系

- 可并行项：
  - `v1.3.0` release planning index
  - `2026-S25` sprint index
  - Batch 0 inventory artifact
- 串行依赖项：
  - spec suite 需要先消费 Batch 0 inventory 中的场景矩阵与错误分类。
  - 后续 runtime/consumer/evidence Work Item 必须等待本 Work Item 合入。
- 阻塞项：
  - 若 `spec review` 未通过，不得创建 runtime implementation Work Item。

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] 关键依赖可用
