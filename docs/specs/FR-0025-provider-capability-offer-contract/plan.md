# FR-0025 Provider capability offer contract 实施计划

## 关联信息

- item_key：`FR-0025-provider-capability-offer-contract`
- Issue：`#297`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 exec-plan：`docs/exec-plans/CHORE-0319-fr-0025-formal-spec-closeout.md`

## 实施目标

- 在进入 offer manifest validator、SDK docs / evidence、父 FR closeout 与 `FR-0026` compatibility decision 之前，冻结 Provider capability offer 的 canonical carrier、字段语义、`FR-0024` requirement input 边界、`FR-0027` resource profile/proof binding、error/version/evidence/lifecycle/observability/fail-closed 边界，使后续实现 Work Item 只能消费同一 offer truth。

## 分阶段拆分

- 阶段 1：`#319` 收口 `FR-0025` formal spec 套件，冻结 `ProviderCapabilityOffer` carrier 与禁止边界。
- 阶段 2：`#320` 基于本 spec 实现 Provider offer manifest fixture / validator 入口，证明 carrier 可被机器校验。
- 阶段 3：`#321` 基于本 spec 补齐 SDK docs / evidence，说明 Provider offer 如何作为 Adapter-bound 能力被声明与追溯。
- 阶段 4：`#322` 汇总 formal spec、validator、SDK docs / evidence、GitHub 状态与 closeout evidence，完成父 FR `#297` closeout。
- 阶段 5：`FR-0026` 消费本 FR 作为 Provider offer input，并与 `FR-0024` requirement input 一起定义 compatibility decision；不得反向改写本 carrier。

## 实现约束

- 不允许触碰的边界：
  - `#319` 不得修改 `syvert/**`、`tests/**`、reference adapter runtime、manifest validator、contract test 代码、`.github/**` 或 `scripts/**`。
  - 不得定义 `AdapterCapabilityRequirement x ProviderCapabilityOffer` compatibility decision。
  - 不得引入 provider selector、provider routing、profile priority、profile fallback、score、marketplace 或真实 provider 产品支持。
  - 不得新增共享能力词汇；resource support 只消费 `FR-0027` 已批准模型。
  - 不得引入 Core provider discovery / registry / routing，或 provider-owned resource lifecycle。
  - 不得关闭父 FR `#297`。
- 与上位文档的一致性约束：
  - 必须满足 `AGENTS.md` 对 formal spec 与实现分离的要求。
  - 必须满足 `WORKFLOW.md` 对 Work Item active exec-plan、事项上下文与 checkpoint 的要求。
  - 必须满足 `spec_review.md` 对 formal spec 最小套件、GWT、异常边界、验收标准与进入实现前条件的要求。
  - 必须把 `FR-0024` 作为 Adapter requirement input，把 `FR-0027` 作为 resource profile / proof binding governing artifact，而不是重建第二套 requirement 或 profile truth。

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-319-fr-0025-provider-capability-offer-formal-spec`
  - `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
- implementation 阶段：
  - `#320` 必须补 offer manifest fixture / validator tests，覆盖缺字段、adapter binding 越界、proof 不对齐、禁止 decision/selector/priority/fallback/marketplace 字段与合法 carrier。
  - `#321` 必须补 SDK docs / evidence，证明 Provider offer 是 Adapter-bound 能力声明，不是 Core discovery / routing 或真实 provider 产品支持。
  - `#322` 必须核对 formal spec、validator、docs / evidence、GitHub issue 状态与 release/sprint 索引一致。
- 手动验证：
  - 核对 `ProviderCapabilityOffer` 字段是否完整覆盖 provider key、adapter binding、capability offer、resource support、error carrier、version、evidence、lifecycle、observability 与 fail-closed。
  - 核对 `resource_support` 是否只消费 `FR-0027`，没有重写 profile tuple、proof binding、matcher 或 compatibility decision。
  - 核对 out of scope 是否明确排除 provider selector、priority、fallback、marketplace、真实 provider 产品支持、Core provider discovery / routing、runtime implementation 与关闭 `#297`。

## TDD 范围

- 先写测试的模块：
  - 本事项为 formal spec closeout，不涉及 runtime 或测试文件变更。
- 暂不纳入 TDD 的模块与理由：
  - offer manifest fixture / validator / contract tests 属于 `#320`。
  - SDK docs / evidence 属于 `#321`。
  - 父 FR closeout / reconciliation 属于 `#322`。
  - compatibility decision tests 属于 `FR-0026` 后续 Work Item。

## 并行 / 串行关系

- 可并行项：
  - `#310/#314` 可在各自 ownership 范围内推进，但不得修改本 FR formal spec 套件。
  - 在 `#319` review 期间，可只读梳理 offer manifest、SDK 文档与 provider port 证据，为 `#320/#321` 做准备。
- 串行依赖项：
  - `#320` 与 `#321` 进入正式执行前，必须先消费本 FR 已冻结的 carrier 与 fail-closed 边界。
  - `#322` 必须等待 `#319/#320/#321` 主干事实齐备后再收口。
  - `FR-0026` compatibility decision 必须等待 `FR-0024` requirement input 与本 FR offer input 都已冻结后再定义 decision。
- 阻塞项：
  - 若 `FR-0025` 不先冻结 offer carrier，后续 validator、SDK docs 与 compatibility decision 会各自发明 provider offer shape。

## 进入实现前条件

- [ ] `spec review` 已通过。
- [ ] `FR-0025` 已明确 `ProviderCapabilityOffer` carrier 与固定字段。
- [ ] `FR-0025` 已明确 provider key 与 adapter binding 只在 Adapter-bound provider port 内有效。
- [ ] `FR-0025` 已明确 capability offer 与 resource support 只覆盖当前 approved slice，并消费 `FR-0027` profile / proof binding。
- [ ] `FR-0025` 已明确 error carrier、version、evidence、lifecycle、observability 与 fail-closed 边界。
- [ ] `FR-0025` 已明确禁止 compatibility decision、provider selector、priority、fallback、marketplace、真实 provider 产品支持、Core discovery / routing 与 runtime 实现。
- [ ] `#320/#321/#322` 的进入条件均可直接回指 `FR-0025` formal spec。
