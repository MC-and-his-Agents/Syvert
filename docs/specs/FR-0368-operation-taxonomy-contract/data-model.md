# FR-0368 数据模型

## OperationTaxonomyEntry

- 作用：定义一个 public operation 如何投影到 Adapter capability family、target type 与 execution / collection mode。
- 稳定性：`v1.1.0` taxonomy canonical carrier。
- 字段：
  - `capability_family`：Adapter-facing capability family，例如 `content_detail`。
  - `operation`：Core public operation，例如 `content_detail_by_url`。
  - `target_type`：输入 target 类型，例如 `url`。
  - `execution_mode`：执行模式，例如 `hybrid`。
  - `collection_mode`：集合语义；当前 baseline 使用 `hybrid` 与既有字段保持一致。
  - `lifecycle`：`proposed`、`experimental`、`stable`、`deprecated`。
  - `runtime_delivery`：是否允许被 stable runtime / compatibility decision 当作 executable capability。
  - `contract_refs`：formal spec、test 或 evidence refs。
  - `admission_evidence_refs`：进入当前 lifecycle 所需 evidence。
  - `notes`：非规范说明，不得承载平台私有字段。

## CapabilityLifecycle

- `proposed`：候选能力，只能用于 taxonomy 表达、规划和 evidence sketch；不得执行。
- `experimental`：已通过独立 FR 批准的实验能力；不得被误标为 stable。
- `stable`：可被 Adapter requirement、Provider offer 与 compatibility decision 消费的正式能力。
- `deprecated`：保留兼容或迁移语义；不得作为新的 stable lookup 结果。

## AdmissionReport

- 作用：表达 taxonomy validator 对 registry 或 entry 的判定。
- 字段：
  - `status`：`admitted`、`rejected`、`invalid_contract`。
  - `capability_family`
  - `operation`
  - `target_type`
  - `execution_mode`
  - `collection_mode`
  - `lifecycle`
  - `runtime_delivery`
  - `failure_category`
  - `error_code`
  - `evidence_refs`
  - `fail_closed`

## Stable baseline

- `capability_family=content_detail`
- `operation=content_detail_by_url`
- `target_type=url`
- `execution_mode=hybrid`
- `collection_mode=hybrid`
- `lifecycle=stable`
- `runtime_delivery=true`

## Proposed reserved candidates

以下候选只能以 `lifecycle=proposed` 与 `runtime_delivery=false` 出现：

这些名称是 reserved capability family，不自动成为后续 stable public executable operation 名称。后续 FR 若把某个 family 升级为 executable slice，必须明确冻结具体 operation 名、target type、execution mode 与 collection mode。

- `content_search`
- `content_list`
- `comment_collection`
- `creator_profile`
- `media_asset_fetch`
- `media_upload`
- `content_publish`
- `batch_execution`
- `scheduled_execution`
- `dataset_sink`

## 状态规则

- `stable + runtime_delivery=true` 是 stable lookup 的必要条件。
- `proposed + runtime_delivery=false` 是 reserved candidate 的固定表达。
- `experimental` 与 `deprecated` 不得由 `v1.1.0` 自动批准。
- 缺少 contract refs 或 evidence refs 的 `stable` entry 必须 invalid。
- 出现 provider selector、fallback、marketplace、平台私有对象或上层 workflow 字段时必须 invalid。
