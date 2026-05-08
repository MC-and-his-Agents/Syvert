# FR-0355 v0.9.0 real provider compatibility evidence

## 关联信息

- item_key：`FR-0355-v0-9-real-provider-compatibility-evidence`
- Issue：`#355`
- item_type：`FR`
- release：`v0.9.0`
- sprint：`2026-S22`
- 上位 Phase：`#354`
- 关联执行事项：`#356 / CHORE-0356-v0-9-provider-compatibility-spec`

## 背景与目标

- 背景：`v0.8.0` 已冻结第三方 Adapter 接入路径、`AdapterCapabilityRequirement`、`ProviderCapabilityOffer`、`AdapterProviderCompatibilityDecision` 与 provider no-leakage guard。`v1.0.0` Core stable gate 已由 `FR-0351` 冻结，并要求 `v0.9.0 provider sample evidence` 作为 `provider_compatibility_sample` 的必要输入。
- 目标：冻结 `v0.9.0` 真实外部 provider compatibility evidence 的最小 contract，使后续 implementation Work Item 可以用非仓内 native provider 的样本证明 requirement -> offer -> decision 链路可执行、可审计、可 fail-closed，同时不声明任何指定 provider 产品正式支持。

## 范围

- 本次纳入：
  - 冻结 `v0.9.0` provider sample evidence 的语义、最小字段与 fail-closed 判定。
  - 要求样本至少覆盖一个已批准 Adapter capability slice：当前只能是 `content_detail + content_detail_by_url + url + hybrid`。
  - 要求样本消费 `FR-0024`、`FR-0025`、`FR-0026`、`FR-0027` 与 `FR-0351`，不得重定义 carrier。
  - 要求 evidence 同时证明 `matched`、`unmatched`、`invalid_contract` 的可复验边界。
  - 要求 evidence 证明 `matched` 后的 Adapter-bound execution boundary 可执行，并覆盖 provider 错误、资源、生命周期与观测证据。
  - 要求 provider 信息不得进入 Core routing、registry discovery、TaskRecord、resource lifecycle 或 Core-facing failed envelope。
  - 要求双参考基线、第三方 Adapter-only entry 与 API / CLI same Core path 在 `v0.9.0` closeout 中持续通过。
- 本次不纳入：
  - runtime、Adapter、Provider、tests、scripts 或 CI 代码变更。
  - 真实 provider sample artifact 的具体实现。
  - provider selector、fallback、priority、ranking、marketplace 或 Core provider registry。
  - 指定 provider 产品正式支持、SLA、可用性承诺或支持清单。
  - 上层应用能力、Python package publish、新 public operation、search/list/comment/batch/dataset 或发布能力。

## 需求说明

- 功能需求：
  - `v0.9.0` 必须生成可被 `FR-0351` 的 `provider_compatibility_sample` gate item 消费的 evidence artifact。
  - evidence 必须使用至少一个非仓内 native provider 的 Adapter-bound provider sample；该样本可以是受控记录、fixture 或 manifest，但必须能证明外部 provider 作者路径，而不是复用 `native_xhs_detail` 或 `native_douyin_detail` 自证。
  - evidence 必须消费现有 validators / runtime decision，而不是复制一套 provider sample 私有判断规则。
  - evidence 必须至少覆盖一个合法 `matched` decision，证明 `AdapterCapabilityRequirement -> ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision` 在 approved slice 上可执行。
  - evidence 必须至少覆盖一个 Adapter-bound execution sample，证明 `matched` decision 可以进入 Adapter-owned provider seam，并产出可审计 raw payload、normalized result 或经 Adapter 映射后的 failed envelope。
  - Adapter-bound execution evidence 必须记录 provider 错误映射、resource profile consumption、resource lifecycle disposition hint 与 observability carrier；这些记录不得泄漏到 Core-facing surfaces。
  - evidence 必须至少覆盖一个合法 `unmatched` decision，证明合法输入没有 resource profile 交集时不会被错误提升为 `matched`。
  - evidence 必须至少覆盖一个 `invalid_contract` decision，证明非法 offer、跨 Adapter binding、execution slice 漂移或 forbidden provider field 会 fail-closed。
  - evidence 必须引用 provider no-leakage guard 结果，证明 provider identity 只留在 Adapter-bound evidence，不进入 Core-facing surfaces。
  - evidence 必须引用双参考 `content_detail_by_url` regression、第三方 Adapter-only contract entry 与 API / CLI same Core path 的验证结果。
- 契约需求：
  - sample evidence 必须声明 `sample_origin=external_provider_sample` 或等价语义，且明确不是 Syvert native provider。
  - sample evidence 必须声明 `provider_support_claim=false`，不得把 sample 解释为 provider 产品正式支持。
  - sample evidence 必须绑定 `FR-0024` requirement ref、`FR-0025` offer ref、`FR-0026` decision ref、`FR-0027` profile proof ref 与 `FR-0351` gate item ref。
  - sample evidence 必须绑定 Adapter-bound execution evidence ref；缺少该 ref 时不得通过 `provider_compatibility_sample`。
  - sample evidence 必须记录 `approved_slice`，当前固定为 `capability=content_detail + operation=content_detail_by_url + target_type=url + collection_mode=hybrid`。
  - sample evidence 的 Core-facing projection 只能暴露无 provider identity 的 status / error 摘要。
  - 任一 required evidence 缺失、只有会话描述、无法从仓内 artifact / tests / PR / issue 复验，或声明 provider 产品正式支持时，`v0.9.0` closeout 必须 fail-closed。
- 非功能需求：
  - evidence 必须可由 reviewer、guardian、release closeout Work Item 与未来自动化共同复验。
  - evidence 不得要求访问真实账号、私密 provider 配置、上层应用仓库或商业 provider 控制台才能判断 Core stable gate。
  - evidence 必须保持 Syvert 是底座，不把外部 provider sample 变成上层 APP 或 provider marketplace。

## 约束

- 阶段约束：
  - 本 FR 服务 `v0.9.0`，目标是为 `v1.0.0` Core stable gate 提供 provider sample evidence。
  - 当前 approved capability slice 不扩展；新 capability、operation、target 或 collection mode 必须进入 `v1.x` 候选或独立 FR。
  - `v0.9.0` 可以交付 evidence 与 release closeout，但不得提前声明 `v1.0.0` Core stable。
- 架构约束：
  - `FR-0024` 继续持有 Adapter capability requirement truth。
  - `FR-0025` 继续持有 Provider capability offer truth。
  - `FR-0026` 继续持有 compatibility decision truth。
  - `FR-0027` 继续持有 resource profile / proof truth。
  - `FR-0351` 继续持有 `v1.0.0` release gate truth。
  - Core 继续只调用 Adapter；Provider 只能作为 Adapter-bound execution capability 参与 compatibility decision。

## GWT 验收场景

### 场景 1：真实外部 provider 样本返回 matched

Given 外部 provider sample 的 `ProviderCapabilityOffer` 合法绑定某个 Adapter，并声明 approved slice
When 该 offer 与同 Adapter 的合法 `AdapterCapabilityRequirement` 进入 `AdapterProviderCompatibilityDecision`
Then decision 必须返回 `matched`
And evidence 必须记录 requirement ref、offer ref、decision ref、profile proof ref 与 no-leakage ref

### 场景 2：合法输入无 profile 交集返回 unmatched

Given 外部 provider sample offer 合法，但 supported profile 不能满足 requirement profile
When compatibility decision 消费这两个输入
Then decision 必须返回 `unmatched`
And closeout 不得把合法不兼容误报为 contract violation

### 场景 3：matched 后必须有 Adapter-bound execution evidence

Given 外部 provider sample 已产生 `matched` decision
When Adapter-owned provider seam 消费该 matched decision 执行 approved capability slice
Then evidence 必须记录 raw payload、normalized result 或经 Adapter 映射后的 failed envelope
And evidence 必须覆盖 provider 错误映射、resource profile consumption、resource lifecycle disposition hint 与 observability carrier
And provider identity 只能留在 Adapter-bound evidence，不得进入 Core-facing projection

### 场景 4：非法 provider sample fail-closed

Given 外部 provider sample offer 出现 forbidden provider selector、fallback、routing、marketplace 或跨 Adapter binding
When compatibility decision 或 validator 消费该 offer
Then decision 必须返回 `invalid_contract`
And `v0.9.0` evidence 不得用该样本通过 `provider_compatibility_sample`

### 场景 5：provider identity 不进入 Core surface

Given decision evidence 在 Adapter-bound carrier 中记录 provider identity
When Core registry discovery、Core routing、TaskRecord、resource lifecycle 或 Core-facing failed envelope 被审计
Then 这些 surface 不得出现 provider key、offer id、selector、fallback、routing 或 provider lifecycle 字段

### 场景 6：双参考基线不可由 provider sample 替代

Given 外部 provider sample evidence 已通过
When 小红书或抖音 `content_detail_by_url` 双参考 regression 失败
Then `v0.9.0` closeout 必须失败
And 不得用 provider sample 替代双参考基线

### 场景 7：样本 evidence 不等于 provider 产品支持

Given external provider sample evidence 已生成
When release index、SDK docs 或 closeout 描述该 evidence
Then 只能声明 compatibility decision 链路被真实外部样本验证
And 不得声明指定 provider 产品正式支持、SLA、marketplace listing 或 Core 可直接调用 provider

## 异常与边界场景

- 如果 external provider sample 只有会话描述、未入库 fixture / artifact 或无法从 PR / tests 复验，应视为缺少 evidence。
- 如果 sample evidence 使用 `native_xhs_detail` 或 `native_douyin_detail` 作为唯一 provider，应视为仍停留在仓内自证，不满足本 FR。
- 如果 sample evidence 只有 decision matrix、没有 Adapter-bound execution evidence，应视为未满足 `FR-0351` 的 `ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision -> Adapter-bound execution evidence` 链路。
- 如果 sample evidence 需要真实账号、私密 token 或 provider 控制台才能判断，应补充脱敏记录或 fixture；否则不得作为 release gate required evidence。
- 如果 implementation 发现现有 validators 无法表达外部 sample，必须通过独立实现 Work Item 修复 runtime / validator，不得在 evidence artifact 中绕过 contract。
- 如果 provider sample 暴露出新 public operation 需求，应降级为 `v1.x` 候选，不得在 `v0.9.0` 中顺手扩大 approved slice。

## 验收标准

- [ ] formal spec 明确 `v0.9.0` provider sample evidence 的最小字段、来源与 fail-closed 条件。
- [ ] formal spec 明确真实外部 provider sample 不等于 provider 产品正式支持。
- [ ] formal spec 明确 sample 必须消费 `FR-0024`、`FR-0025`、`FR-0026`、`FR-0027` 与 `FR-0351`。
- [ ] formal spec 明确必须覆盖 `matched`、`unmatched` 与 `invalid_contract`。
- [ ] formal spec 明确必须覆盖 Adapter-bound execution evidence、provider 错误、资源、生命周期与观测证据。
- [ ] formal spec 明确 provider identity 不得进入 Core-facing surfaces。
- [ ] formal spec 明确双参考、第三方 Adapter-only entry 与 API / CLI same Core path 是 `v0.9.0` closeout required evidence。
- [ ] formal spec 不修改 runtime、Adapter、Provider、tests、scripts 或 CI。

## 依赖与外部前提

- 外部依赖：
  - `FR-0024` / `FR-0025` / `FR-0026` / `FR-0027` 已合入并完成 v0.8.0 closeout。
  - `FR-0351` 已冻结 `v1.0.0` Core stable release gate。
- 上下游影响：
  - 后续 implementation Work Item 必须基于本 FR 交付 provider sample fixture / artifact、runtime tests、no-leakage evidence、release index 与 closeout。
  - `v1.0.0` release closeout 必须消费本 FR 的 merged evidence，而不是重新解释 provider sample gate。
