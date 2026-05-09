# FR-0404 Comment collection contract 实施计划

## 关联信息

- item_key：`FR-0404-comment-collection-contract`
- Issue：`#404`
- item_type：`FR`
- release：`v1.4.0`
- sprint：`2026-S25`
- 关联 exec-plan：`docs/exec-plans/CHORE-0416-v1-4-comment-collection-spec.md`

## 实施目标

- 本次实施只交付 `FR-0404` 的 Batch 0 inventory 与 Batch 1 formal spec suite。
- 后续 Work Item 才允许实现 runtime carrier、consumer migration、fake/reference evidence 与 release closeout。

## 分阶段拆分

- 阶段 1：`#416` 冻结 Batch 0 comment fixture/error inventory，形成 reviewable hierarchy/visibility/cursor matrix 与公共错误分类。
- 阶段 2：`#416` 冻结 `FR-0404` formal spec、data model、contract README 与 risks。
- 阶段 3：`#417` 实现 comment runtime carrier。
- 阶段 3A：`#417` 同步把 `FR-0368` 中的 comment capability candidate 升级为 `FR-0404` 的 executable runtime slice：public operation `comment_list_by_content` 投影到 `comment_collection + content + single + paginated`，并更新 operation taxonomy 与 runtime-delivery truth。
- 阶段 4：`#418` 迁移 TaskRecord / result query / compatibility decision 等 consumers，并把 requirement/offer/compatibility baseline 对齐到 `comment_list_by_content -> comment_collection + content + single + paginated` executable slice。
- 阶段 5：`#419` 补齐 fake/reference evidence。
- 阶段 6：`#420` 完成 `v1.4.0` release closeout 与 published truth carrier。

## 实现约束

- 不允许触碰 runtime、tests implementation、raw fixture payload files。
- 不允许把 creator profile、media download/no-download boundary 混入 `FR-0404`。
- 不允许在 repository 或 GitHub truth 中出现外部项目名或本地路径。
- 不允许把 `v1.4.0` 写成整个 Phase 3 的 release 绑定。
- 不允许修改 `content_detail_by_url` baseline 或 `FR-0403` public behavior。
- 不允许把 taxonomy proposed-candidate -> executable-slice 的升级留到实现 PR 自由解释；该升级路径必须由 `#417/#418` 明确承接。

## 测试与验证策略

- 单元测试：本 Work Item 不新增 runtime 单元测试。
- 集成/契约测试：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `python3 scripts/version_guard.py --mode ci`
  - `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `git diff --check`
- 手动验证：
  - 核对 `#381/#404/#416` truth 与 `v1.4.0` / `2026-S25` planning truth 一致。
  - 搜索变更内容，确认不含外部项目名或本地路径。
  - 用 `spec_review.md` rubric 做 formal spec review。

## 当前验证结果

- 已执行：
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
  - 脱敏搜索：未命中外部项目名或本地路径。
- 未执行：
  - runtime / consumer / evidence replay tests
    - 理由：由 `#417/#418/#419` 分别承接，不在本 Work Item 范围。

## TDD 范围

- 先写测试的模块：不适用，本 Work Item 只交付 formal spec 与 planning truth。
- 暂不纳入 TDD 的模块与理由：runtime carrier、consumer migration 与 evidence replay 均由后续 Work Item 承接。

## 并行 / 串行关系

- 可并行项：
  - `v1.4.0` release planning index
  - `2026-S25` sprint update
  - Batch 0 inventory artifact
- 串行依赖项：
  - spec suite 需要先消费 Batch 0 inventory 中的 hierarchy/visibility/cursor 场景矩阵与错误分类。
  - 后续 runtime/consumer/evidence Work Item 必须等待本 Work Item 合入。
- 阻塞项：
  - 若 `spec review` 未通过，不得创建 runtime implementation PR。

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] 关键依赖可用
