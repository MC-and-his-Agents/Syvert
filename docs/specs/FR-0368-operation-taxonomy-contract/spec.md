# FR-0368 Operation taxonomy and capability admission contract

## 关联信息

- item_key：`CHORE-0369-v1-1-operation-taxonomy-spec`
- Issue：`#369`
- item_type：`CHORE`
- release：`v1.1.0`
- sprint：`2026-S23`
- Parent Phase：`#367`
- Parent FR：`#368`

## 背景与目标

- 背景：`v1.0.0` 已冻结 Core / Adapter / Provider compatibility baseline，当前唯一 stable execution slice 是 `content_detail + content_detail_by_url + url + hybrid`。`v1.x` 后续 read-side、batch / dataset、scheduled execution 与 write-side capability 都需要统一的 operation taxonomy 与准入机制，否则会退化为 Adapter 私有接口集合。
- 目标：冻结 `v1.1.0` Operation Taxonomy Foundation 的 canonical taxonomy model、capability lifecycle、候选能力准入规则、禁止边界与后续 contract consumer 的消费方式。

## 范围

- 本次纳入：
  - `OperationTaxonomyEntry` canonical model。
  - operation / adapter-facing capability family / target type / execution mode / collection mode 的命名规则。
  - public operation 到 Adapter capability 的投影规则。
  - capability lifecycle：`proposed`、`experimental`、`stable`、`deprecated`。
  - `AdmissionReport` 与 fail-closed 规则。
  - 候选能力族的 `proposed` registry 语义。
  - Adapter requirement、Provider offer 与 compatibility decision 对 taxonomy 的消费边界。
- 本次不纳入：
  - `content_search`、`content_list`、`comment_collection`、`creator_profile`、`media_asset_fetch`、`media_upload`、`content_publish`、`batch_execution`、`scheduled_execution`、`dataset_sink` 的 runtime implementation。
  - 新 public executable operation。
  - provider selector、fallback、priority、ranking 或 marketplace。
  - 上层应用 workflow、内容库、自动运营或产品 UI。
  - Python package publish。

## 需求说明

- 功能需求：
  - taxonomy 必须能表达唯一 stable baseline：`content_detail + content_detail_by_url + url + hybrid`。
  - taxonomy 必须能登记候选能力族，但候选能力族只能作为 `lifecycle=proposed` 且 `runtime_delivery=false` 的 reserved candidate。
  - stable lookup 只能返回 `lifecycle=stable` 且 `runtime_delivery=true` 的 entry。
  - proposed / experimental / deprecated entry 不得被 Adapter requirement、Provider offer 或 compatibility decision 当作可执行 stable contract。
  - operation 命名必须全局唯一；同一 operation 不得映射到多个 capability family、target type 或 mode。
  - taxonomy 必须提供 admission result，区分 `admitted`、`rejected` 与 `invalid_contract`。
- 契约需求：
  - `AdapterCapabilityRequirement`、`ProviderCapabilityOffer` 与 `AdapterProviderCompatibilityDecision` 后续只能消费 taxonomy 的 stable execution slice。
  - 当前 stable baseline 的行为必须保持与 `v1.0.0` 一致。
  - 候选能力从 `proposed` 升级到 `experimental` 或 `stable` 必须另走独立 FR、formal spec、contract test、双参考或等价 evidence。
  - proposed reserved candidate 名称表达 capability family；后续独立 FR 可以冻结更具体的 public executable operation 名称，并必须在 promotion 时保持 `capability_family / operation / target_type / execution_mode / collection_mode` 单一映射。
  - `content_detail_by_url` baseline 不得被候选能力、mode 扩展或 target type 扩展改写。
- 非功能需求：
  - taxonomy 必须 fail-closed；无法证明 entry 合法、唯一、无泄漏或生命周期允许时，不得返回 stable execution slice。
  - taxonomy 不能包含平台私有对象、provider 产品支持承诺、provider routing 或上层 workflow 字段。
  - taxonomy 文档、runtime carrier 与 SDK 文档必须共享同一语义。

## 约束

- 阶段约束：
  - `v1.1.0` 只交付 taxonomy / admission / validation foundation。
  - `content_detail_by_url` 是唯一 stable baseline。
  - 候选能力族最多进入 `proposed`，不能在本 release 中成为 stable runtime capability。
- 架构约束：
  - Core 只理解 public operation、target、mode、task envelope、resource admission 与 result envelope。
  - Adapter 负责平台参数、平台对象与 normalized result。
  - Provider 只通过 Adapter-bound provider offer 参与执行能力声明，不定义 Syvert public operation vocabulary。

## GWT 验收场景

### 场景 1：stable baseline 可以被 taxonomy 表达

Given taxonomy registry 包含 `content_detail + content_detail_by_url + url + hybrid`
When Adapter requirement、Provider offer 或 compatibility decision 查询该 execution slice
Then stable lookup 返回唯一 stable entry，且行为与 `v1.0.0` baseline 一致

### 场景 2：proposed candidate 不得成为 executable runtime capability

Given taxonomy registry 包含 `content_search` 或 `comment_collection` 的 proposed entry
When stable lookup 或 compatibility decision 尝试将其作为 executable capability 使用
Then lookup 必须 fail-closed，且不得返回 `matched`

### 场景 3：operation 命名冲突必须被拒绝

Given 两条 entry 使用同一个 public operation 但 capability family、target type 或 mode 不同
When taxonomy validator 校验 registry
Then admission report 必须返回 `invalid_contract`

### 场景 4：候选能力升级必须另走 FR

Given `content_search` 处于 `proposed`
When 有实现尝试将其标记为 `stable`
Then 必须要求独立 FR / formal spec / contract test / 双参考或等价 evidence；本 FR 不得直接批准该升级

### 场景 5：provider selector 字段不得进入 taxonomy

Given taxonomy entry 包含 `provider_selector`、`fallback`、`marketplace` 或平台私有对象字段
When taxonomy validator 校验 entry
Then admission report 必须返回 `invalid_contract`

## 异常与边界场景

- 缺少 capability family、operation、target type、mode、lifecycle 或 runtime delivery 字段时，entry invalid。
- `lifecycle=stable` 但 `runtime_delivery=false` 时，entry invalid。
- `lifecycle=proposed` 但 `runtime_delivery=true` 时，entry invalid。
- `deprecated` entry 不得作为 stable execution slice 返回。
- target type 或 mode 与 current stable baseline 不一致时，不得影响 `content_detail_by_url` baseline。

## 验收标准

- [ ] formal spec 冻结 operation taxonomy canonical model。
- [ ] formal spec 明确 `content_detail_by_url` 是唯一 stable baseline。
- [ ] formal spec 明确候选能力族只能作为 `proposed` reserved candidates。
- [ ] formal spec 明确 candidate 从 `proposed` 升级必须另走独立 FR。
- [ ] formal spec 明确 Adapter requirement、Provider offer 与 compatibility decision 必须消费 stable taxonomy entry。
- [ ] formal spec 明确 provider selector、fallback、marketplace、平台私有对象和上层 workflow 不得进入 taxonomy。
- [ ] 本事项不修改 runtime、Adapter、Provider 或 SDK 实现。

## 依赖与外部前提

- `v1.0.0` Core stable release 已完成。
- `FR-0351` 已冻结 Core stable release gate。
- `FR-0024`、`FR-0025` 与 `FR-0026` 已冻结 Adapter requirement、Provider offer 与 compatibility decision baseline。
- `v0.9.0` real provider sample evidence 已完成。
