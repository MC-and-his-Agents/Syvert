# FR-0026 Adapter provider compatibility decision 实施计划

## 关联信息

- item_key：`FR-0026-adapter-provider-compatibility-decision`
- Issue：`#298`
- item_type：`FR`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 exec-plan：`docs/exec-plans/CHORE-0323-fr-0026-formal-spec-closeout.md`

## 实施目标

- 在进入 compatibility decision runtime、provider no-leakage guard、docs / evidence 与父 FR closeout 之前，冻结 `AdapterCapabilityRequirement x ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision` 的输入、输出、状态、错误 carrier、fail-closed 与 no-leakage 语义，使后续实现只消费 `FR-0024`、`FR-0025` 与 `FR-0027` 的已批准 contract。

## 分阶段拆分

- 阶段 1：`#323` 收口 `FR-0026` formal spec 套件，冻结 decision carrier、判定规则与禁止边界。
- 阶段 2：`#324` 基于本 spec 实现 compatibility decision runtime，覆盖 `matched`、`unmatched`、`invalid_contract` 与 fail-closed。
- 阶段 3：`#325` 基于本 spec 实现 provider no-leakage guards，证明 provider 信息不进入 Core routing、registry discovery、TaskRecord 或 resource lifecycle。
- 阶段 4：`#326` 基于本 spec 补齐 docs / evidence，说明 Adapter-bound compatibility decision 的解释边界。
- 阶段 5：`#327` 汇总 formal spec、runtime、guard、docs / evidence、GitHub 状态与 closeout evidence，完成父 FR `#298` closeout。

## 实现约束

- 不允许触碰的边界：
  - `#323` 不得修改 `syvert/**`、`tests/**`、`scripts/**`、reference adapter runtime、manifest validator、contract test 代码或 `.github/**`。
  - 不得修改既有 `FR-0023`、`FR-0024`、`FR-0025` 或 `FR-0027` formal spec。
  - 不得定义 requirement carrier、offer carrier 或 resource profile carrier 本体。
  - 不得引入 provider selector、provider routing、profile priority、profile fallback、score、ranking、marketplace 或真实 provider 产品支持。
  - 不得新增 Core provider discovery / registry / routing、provider-owned resource lifecycle 或 provider resource supply。
  - 不得关闭父 FR `#298`。
- 与上位文档的一致性约束：
  - 必须满足 `AGENTS.md` 对 formal spec 与实现分离的要求。
  - 必须满足 `WORKFLOW.md` 对 Work Item active exec-plan、事项上下文与 checkpoint 的要求。
  - 必须满足 `spec_review.md` 对 formal spec 最小套件、GWT、异常边界、验收标准与进入实现前条件的要求。
  - 必须把 `FR-0024` 作为 Adapter requirement input，把 `FR-0025` 作为 Provider offer input，把 `FR-0027` 作为 resource profile / proof binding governing artifact。

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-323-fr-0026-compatibility-decision-formal-spec`
  - `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
- implementation 阶段：
  - `#324` 必须补 runtime tests，覆盖合法 matched、合法 unmatched、invalid requirement、invalid offer、adapter mismatch、execution mismatch、proof mismatch 与禁止字段。
  - `#325` 必须补 no-leakage guard tests，覆盖 Core registry discovery、Core routing、TaskRecord 与 resource lifecycle 均无 provider 字段。
  - `#326` 必须补 docs / evidence，证明 decision 只表达 Adapter-bound compatibility，不表达 provider selector 或产品支持。
  - `#327` 必须核对 formal spec、runtime、guard、docs / evidence、GitHub issue 状态与 release/sprint 索引一致。
- 手动验证：
  - 核对 decision 状态是否只允许 `matched`、`unmatched`、`invalid_contract`。
  - 核对 unmatched 与 invalid_contract 是否保持可区分。
  - 核对 provider key 只出现在 Adapter-bound evidence，不进入 Core-facing surface。

## TDD 范围

- 先写测试的模块：
  - 本事项为 formal spec closeout，不涉及 runtime 或测试文件变更。
- 暂不纳入 TDD 的模块与理由：
  - compatibility decision runtime tests 属于 `#324`。
  - no-leakage guard tests 属于 `#325`。
  - docs / evidence 验证属于 `#326`。
  - 父 FR closeout / reconciliation 属于 `#327`。

## 并行 / 串行关系

- 可并行项：
  - 在 `#323` review 期间，可只读梳理 runtime、Core-facing surface 与 docs / evidence 入口，为 `#324/#325/#326` 做准备。
- 串行依赖项：
  - `#324` 进入正式执行前，必须先消费本 FR 已冻结的 decision status、fail-closed 与 profile matching 规则。
  - `#325` 进入正式执行前，必须先消费本 FR 已冻结的 no-leakage surface。
  - `#326` 进入正式执行前，必须先消费本 FR 对 matched / unmatched / invalid_contract 的解释边界。
  - `#327` 必须等待 `#323/#324/#325/#326` 主干事实齐备后再收口。
- 阻塞项：
  - 若 `FR-0026` 不先冻结 decision contract，runtime、guard、docs 与 closeout 可能各自发明 compatibility truth。

## 进入实现前条件

- [ ] `spec review` 已通过。
- [ ] `FR-0026` 已明确 `AdapterProviderCompatibilityDecision` carrier 与固定字段。
- [ ] `FR-0026` 已明确只消费 `FR-0024`、`FR-0025` 与 `FR-0027`。
- [ ] `FR-0026` 已明确 `matched` / `unmatched` / `invalid_contract` 边界。
- [ ] `FR-0026` 已明确 adapter key、capability、execution slice、resource profile tuple 与 proof coverage 的匹配规则。
- [ ] `FR-0026` 已明确 fail-closed 与 provider no-leakage 约束。
- [ ] `FR-0026` 已明确禁止 provider selector、priority、fallback、routing、marketplace、真实 provider 产品支持、Core discovery / routing 与 runtime 实现。
- [ ] `#324/#325/#326/#327` 的进入条件均可直接回指 `FR-0026` formal spec。
