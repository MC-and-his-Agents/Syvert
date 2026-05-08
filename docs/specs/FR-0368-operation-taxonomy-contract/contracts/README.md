# FR-0368 contracts

## Contract name

`OperationTaxonomyEntry` / `v1.1.0`

## Contract purpose

本 contract 定义 Syvert public operation 与 Adapter-facing capability family 的映射、生命周期和 admission 规则。它是 `AdapterCapabilityRequirement`、`ProviderCapabilityOffer` 与 `AdapterProviderCompatibilityDecision` 后续消费 stable execution slice 的上游 truth。

## Stable consumer rules

- Adapter requirement 只能声明 taxonomy stable lookup 返回的 execution slice。
- Provider offer 只能 offer taxonomy stable lookup 返回的 execution slice。
- Compatibility decision 只能对两侧都属于同一个 stable taxonomy entry 的输入返回 `matched`。
- Proposed candidate 不得返回 `matched`，不得进入 executable runtime capability。

## Forbidden carrier fields

Taxonomy entry、admission report 与 downstream consumer 不得包含：

- provider selector / routing / fallback / priority / ranking
- marketplace / provider product support / SLA
- platform private object names
- upper application workflow
- product UI / content library / automation strategy

## Compatibility rule

`v1.1.0` 必须保持 `content_detail_by_url + url + hybrid` 行为与 `v1.0.0` 一致。任何新增 candidate 都不能改变 Adapter requirement、Provider offer、compatibility decision、TaskRecord、resource lifecycle 或 Core-facing error envelope 的当前语义。
