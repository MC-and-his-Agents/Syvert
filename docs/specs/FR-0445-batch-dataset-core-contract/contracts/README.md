# FR-0445 contracts

## Contract name

`BatchDatasetCoreContract` / `v1.6.0`

## Contract purpose

本 contract 定义 Syvert Core 的首个 batch / dataset foundation。它冻结 batch request、target set、item-level outcome、partial success/failure、resume token、batch audit trace、dataset record 与 dataset sink 最小模型，不交付 scheduler、write-side、内容库、BI、UI 或 provider selector/fallback/marketplace。

## Core ownership rules

- Core 拥有 `batch_execution` public carrier、target set、item outcome、resume token、audit trace、dataset record 与 reference dataset sink contract。
- Core 只封装已稳定 read-side result envelope，不重新定义 creator/comment/media/content 私有字段。
- Core 必须保留 item-level success/failure truth；batch-level partial success 不得吞掉 item-level error。
- Core 必须执行 dataset record validation、dedup first-wins、dataset-id readback、batch-id readback 与 audit replay。
- Core 使用 `adapter_key` / `source_trace` 承载脱敏 adapter identity 与来源追溯；该 identity 必须来自既有 `InputTarget` / read-side envelope，不得引入 provider selector、fallback、platform source name 或 marketplace 语义。
- Core owns dataset identity visibility：`dataset_id` comes from request input or a stable derivation from `batch_id`, and must be surfaced through `BatchResultEnvelope` and `DatasetRecord`.
- Core treats cancel / timeout as runtime stop boundaries: use `resumable` with processed outcome prefix and sanitized audit when a suffix remains.
- Core treats dataset sink write failure as item failure: preserve the read-side result for audit, keep `dataset_record_ref` empty, and aggregate the batch with that item as failed.

## Adapter consumer rules

- Adapter 继续只负责单 item operation 的平台投影。
- Adapter 不接收 batch-level scheduler、provider selector、fallback、marketplace 或 content-library policy。
- Adapter 返回的 read-side envelope 由 Core 封装为 `BatchItemOutcome`；Adapter 不定义 dataset sink schema。

## Resource governance rules

- batch request 本身不要求真实账号、登录态或 resource bundle。
- 每个 item operation 需要资源时，必须继续通过现有 resource governance 和 single item execution path。
- batch audit trace 可引用 resource trace refs，但不得暴露 private account/session/proxy details。

## Dataset sink rules

- Dataset sink contract 只提供 write、dataset-id readback、batch-id readback 与 audit replay。
- Dataset record 必须使用 sanitized adapter key、source trace、evidence ref、raw payload ref 与 JSON-safe normalized payload。
- Dataset sink 不生成 dataset identity；它只接收并索引 Core-provided `dataset_id` / `batch_id`。
- `source_trace.provider_path` may keep the published read-side sanitized opaque execution-path alias; raw provider route/path remains forbidden.
- Sink 不得暴露 storage handle、本地路径、bucket URL、download path 或产品数据库 schema。

## Consumer rules

- TaskRecord consumer 后续只能记录 batch request snapshot、batch result envelope、item outcome refs 与 dataset record refs。
- Result query consumer 后续只能读取 public batch/dataset carriers。
- Compatibility decision 只能验证 operation/capability admission surface，不消费 dataset normalized payload 或 raw payload shape。

## Forbidden carrier fields

以下字段或语义不得进入 Core public batch/dataset contract：

- raw payload inline content
- source names or external project names
- local filesystem paths
- storage handles, bucket URLs, signed URLs, download handles
- private account, session, credential, media, creator, or provider routing fields
- scheduler trigger/rule/coalescing semantics
- write-side publish/upload semantics
- provider selector, fallback, ranking, priority, marketplace, SLA
- content library, BI, analytics product, UI workflow

## Compatibility rule

`v1.6.0` batch/dataset contract consumes `FR-0403`、`FR-0404`、`FR-0405` stable read-side carriers. It must not rewrite those contracts. If a read-side carrier defect is found, create a separate remediation Work Item.
