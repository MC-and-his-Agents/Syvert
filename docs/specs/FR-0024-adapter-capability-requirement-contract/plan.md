# FR-0024 Adapter capability requirement contract 实施计划

## 关联信息

- item_key：`FR-0024-adapter-capability-requirement-contract`
- Issue：`#296`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 exec-plan：`docs/exec-plans/CHORE-0313-fr-0024-formal-spec-closeout.md`

## 实施目标

- 在进入 manifest fixture validator、reference adapter migration 与父 FR closeout 之前，冻结 Adapter capability requirement 的 canonical carrier、字段语义、`FR-0027` resource profile/proof binding、lifecycle/observability/fail-closed 边界，使后续实现 Work Item 只能消费同一 requirement truth。

## 分阶段拆分

- 阶段 1：`#313` 收口 `FR-0024` formal spec 套件，冻结 `AdapterCapabilityRequirement` carrier 与禁止边界。
- 阶段 2：`#314` 基于本 spec 实现 manifest fixture validator / contract test 入口，证明 carrier 可被机器校验。
- 阶段 3：`#315` 基于本 spec 迁移小红书、抖音 reference adapter requirement baseline，不改变 runtime 行为。
- 阶段 4：`#316` 汇总 formal spec、validator、reference adapter migration、GitHub 状态与 closeout evidence，完成父 FR `#296` closeout。
- 阶段 5：后续 Provider offer / compatibility decision FR 消费本 FR 作为 requirement input，但不得反向改写本 carrier。

## 实现约束

- 不允许触碰的边界：
  - `#313` 不得修改 `syvert/**`、`tests/**`、reference adapter runtime、manifest validator 或 contract test 代码。
  - 不得定义 Provider capability offer、compatibility decision、provider selector、provider routing、profile priority 或 profile fallback。
  - 不得新增共享能力词汇；resource profiles 只消费 `FR-0027` 已批准模型。
  - 不得关闭父 FR `#296`。
- 与上位文档的一致性约束：
  - 必须满足 `AGENTS.md` 对 formal spec 与实现分离的要求。
  - 必须满足 `WORKFLOW.md` 对 Work Item active exec-plan、事项上下文与 checkpoint 的要求。
  - 必须满足 `spec_review.md` 对 formal spec 最小套件、GWT、异常边界、验收标准与进入实现前条件的要求。
  - 必须把 `FR-0027` 作为 resource requirement profiles / proof binding 的 governing artifact，而不是重建第二套 profile truth。

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-313-fr-0024-adapter-capability-requirement-formal-spec`
  - `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
- implementation 阶段：
  - `#314` 必须补 manifest fixture / validator tests，覆盖缺字段、proof 不对齐、禁止 provider/priority/fallback 字段与合法 carrier。
  - `#315` 必须补 reference adapter baseline evidence，证明小红书、抖音 requirement 声明消费本 carrier 与 `FR-0027` profile proof。
  - `#316` 必须核对 formal spec、validator、migration、GitHub issue 状态与 release/sprint 索引一致。
- 手动验证：
  - 核对 `AdapterCapabilityRequirement` 字段是否完整覆盖 capability、execution requirement、resource profiles、evidence、lifecycle、observability 与 fail-closed。
  - 核对 `resource_requirement` 是否只消费 `FR-0027`，没有重写 profile tuple、proof binding 或 matcher 语义。
  - 核对 out of scope 是否明确排除 Provider offer、compatibility decision、profile priority/fallback、新共享能力词汇、runtime implementation 与关闭 `#296`。

## TDD 范围

- 先写测试的模块：
  - 本事项为 formal spec closeout，不涉及 runtime 或测试文件变更。
- 暂不纳入 TDD 的模块与理由：
  - manifest fixture validator / contract tests 属于 `#314`。
  - reference adapter requirement migration tests / evidence 属于 `#315`。
  - 父 FR closeout / reconciliation 属于 `#316`。

## 并行 / 串行关系

- 可并行项：
  - 在 `#313` review 期间，可只读梳理 manifest fixture、SDK 文档与 reference adapter 当前声明形态，为 `#314/#315` 做准备。
- 串行依赖项：
  - `#314` 与 `#315` 进入正式执行前，必须先消费本 FR 已冻结的 carrier 与 fail-closed 边界。
  - `#316` 必须等待 `#313/#314/#315` 主干事实齐备后再收口。
- 阻塞项：
  - 若 `FR-0024` 不先冻结 requirement carrier，后续 validator、reference adapter migration 与 compatibility decision 会各自发明 requirement shape。

## 进入实现前条件

- [ ] `spec review` 已通过。
- [ ] `FR-0024` 已明确 `AdapterCapabilityRequirement` carrier 与固定字段。
- [ ] `FR-0024` 已明确消费 `FR-0027` resource requirement profiles / proof binding。
- [ ] `FR-0024` 已明确 lifecycle / observability / fail-closed 边界。
- [ ] `FR-0024` 已明确禁止 Provider offer、compatibility decision、profile priority/fallback、新共享能力词汇、runtime 实现与关闭 `#296`。
- [ ] `#314/#315/#316` 的进入条件均可直接回指 `FR-0024` formal spec。
