# FR-0368 Operation taxonomy contract 实施计划

## 关联信息

- item_key：`CHORE-0369-v1-1-operation-taxonomy-spec`
- Issue：`#369`
- item_type：`CHORE`
- release：`v1.1.0`
- sprint：`2026-S23`
- 关联 exec-plan：`docs/exec-plans/CHORE-0369-v1-1-operation-taxonomy-spec.md`

## 实施目标

- 本次实施只交付 formal spec suite。
- 后续 Work Item 才允许实现 runtime carrier、consumer migration、evidence 与 release closeout。

## 分阶段拆分

- 阶段 1：`#369` 冻结 taxonomy formal spec。
- 阶段 2：`#370` 实现 taxonomy runtime carrier。
- 阶段 3：`#371` 迁移 Adapter requirement、Provider offer 与 compatibility decision。
- 阶段 4：`#372` 补齐 proposed candidate admission evidence。
- 阶段 5：`#373` 完成 `v1.1.0` release closeout。

## 实现约束

- 不允许触碰 runtime、Adapter、Provider、SDK 实现。
- 不允许把候选能力写成 stable runtime capability。
- 不允许修改 `content_detail_by_url` baseline。
- 不允许引入 provider selector、fallback、marketplace 或上层 workflow。

## 测试与验证策略

- 单元测试：本 Work Item 不新增 runtime 单元测试。
- 集成/契约测试：通过 `spec_guard`、`docs_guard`、`workflow_guard` 与 `governance_gate`。
- 手动验证：核对 spec 是否与 `#367/#368/#369` 的 GitHub truth 一致。

## TDD 范围

- 先写测试的模块：不适用，本 Work Item 只交付 formal spec。
- 暂不纳入 TDD 的模块与理由：runtime carrier 与 validator 由 `#370` 承接。

## 并行 / 串行关系

- 可并行项：无。
- 串行依赖项：`#370/#371/#372/#373` 必须等待本 Work Item 合入。
- 阻塞项：如果 spec review 未通过，不得进入 runtime carrier 实现。

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] 关键依赖可用
