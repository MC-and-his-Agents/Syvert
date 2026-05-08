# FR-0387 Resource governance admission and health contract 实施计划

## 关联信息

- item_key：`CHORE-0388-v1-2-resource-governance-spec`
- Issue：`#388`
- item_type：`CHORE`
- release：`v1.2.0`
- sprint：`2026-S24`
- 关联 exec-plan：`docs/exec-plans/CHORE-0388-v1-2-resource-governance-spec.md`

## 实施目标

- 本次实施只交付 formal spec suite。
- 本次不实现 runtime carrier、不迁移 AdapterRequirement / ProviderOffer、不新增 fake/reference evidence、不做 release closeout。

## 分阶段拆分

- 阶段 1：`#388` 冻结 resource governance admission and health formal spec。
- 阶段 2：如果 spec review 后明确需要 runtime carrier，再创建 runtime Work Item。
- 阶段 3：如果 runtime carrier 影响 AdapterRequirement、ProviderOffer 或 compatibility decision，再创建 consumer migration Work Item。
- 阶段 4：如果需要 fake/reference/real evidence 证明边界，再创建 evidence Work Item。
- 阶段 5：release closeout 最后创建 GOV Work Item，消费已合入的 spec、runtime、migration 与 evidence 真相。

## 实现约束

- 不允许修改 `syvert/**`、`tests/**`、SDK 文档或 release index。
- 不允许新增 resource type、public operation、Provider offer 字段或 Adapter requirement 字段。
- 不允许把 `SessionHealth` 实现成第二套 resource lifecycle status。
- 不允许定义自动登录、自动刷新、健康修复循环或后台再验证机制。
- 不允许提前创建 runtime/evidence/release Work Item。

## 测试与验证策略

- 单元测试：本 Work Item 不新增 runtime 单元测试。
- 集成/契约测试：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-388-chore-0388-v1-2-resource-governance-spec`
- 手动验证：
  - 核对 #380 仍只是 Phase。
  - 核对 #387 仍是 FR requirement container。
  - 核对 #388 是唯一进入 execution workspace 的 Work Item。

## TDD 范围

- 先写测试的模块：不适用，本 Work Item 只交付 formal spec。
- 暂不纳入 TDD 的模块与理由：runtime carrier、consumer migration 与 evidence implementation 由后续 Work Item 承接。

## 并行 / 串行关系

- 可并行项：无。本 spec 必须先合入。
- 串行依赖项：runtime carrier、consumer migration、evidence 与 release closeout 均等待本 Work Item 合入后按需拆分。
- 阻塞项：如果 spec review 未通过，不得进入 runtime carrier 实现。

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] 关键依赖可用
