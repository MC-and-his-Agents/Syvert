# FR-0445 Batch / Dataset Core Contract

## 关联信息

- item_key：`FR-0445-batch-dataset-core-contract`
- Issue：`#445`
- item_type：`FR`
- release：`v1.6.0`
- sprint：`2026-S25`
- Parent Phase：`#444`
- Roadmap anchor：`#382` remains deferred/not planned and is not an execution entry

## 背景与目标

- 背景：`v1.1.0` Operation Taxonomy 与 `v1.2.0` Resource Governance 已发布；read-side release slices `v1.3.0`、`v1.4.0`、`v1.5.0` 已发布并提供稳定 read-side result envelope。Phase `#381` closeout 仍由独立事项收口，不作为本 FR 的 completed truth。
- 目标：冻结 `v1.6.0` Batch / Dataset Core formal contract，定义 batch request / target set、item-level outcome、partial success/failure、resume token、batch audit trace、dataset record / sink 最小模型、dataset readback 与 audit replay。

## 范围

- 本次纳入：
  - `batch_execution` 的 Core batch request、target set、item outcome 与 result envelope。
  - batch item operation 复用稳定 read-side operations：`content_search_by_keyword`、`content_list_by_creator`、`comment_collection`、`creator_profile_by_id`、`media_asset_fetch_by_ref`。
  - `BatchResumeToken` 作为 runtime position carrier，不表达业务策略、调度规则或上层 workflow。
  - `DatasetRecord` 与 `DatasetSink` 最小模型，覆盖 write、readback、audit replay 与 dedup。
  - batch-level 与 item-level audit trace，全部使用 sanitized evidence alias。
- 本次不纳入：
  - runtime implementation、tests implementation、raw fixture payload files。
  - scheduled execution、write-side operations、content library、BI / analytics product、UI。
  - provider selector、fallback、marketplace、provider ranking、provider SLA 或 product support list。
  - read-side result envelope 的实体字段重定义。
  - 真实账号/登录态作为 Core batch contract 的前置条件。

## 需求说明

- Core 必须能接收一组 `BatchTargetItem`，每个 item 绑定稳定 read-side operation、脱敏 `adapter_key`、target type、target ref、dedup key 与可选 request cursor；`adapter_key` 复用现有 `InputTarget.adapter_key` 的 Syvert 内部 alias 语义，不得承载平台名、source name、provider route、账号池或 fallback 策略。
- 当 request 绑定 `dataset_sink_ref` 时，`dataset_id` 必须由 caller 提供或由 Core 从 `batch_id` 派生，并在 batch result 与 dataset record 中回显；dataset sink 不生成不可追溯 dataset identity。
- Core 必须为每个已处理 item 生成独立 `BatchItemOutcome`，并保留 item-level success envelope 或 failure envelope；partial failure 不得吞掉 item 级错误。
- Core 必须在 batch-level result 中表达 `complete`、`partial_success`、`all_failed` 与 `resumable`。
- duplicate `dedup_key` 采用 first-wins：第一个 item 正常执行或写入，后续 duplicate item 标记 `duplicate_skipped`，不得写第二份 dataset record。
- `duplicate_skipped` 参与 batch 聚合时按 neutral terminal outcome 处理：若所有非 duplicate item 都 succeeded，batch result 为 `complete`；若至少一个非 duplicate item succeeded 且至少一个 failed，batch result 为 `partial_success`；若所有非 duplicate item 都 failed，batch result 为 `all_failed`；若执行中断且可恢复，batch result 为 `resumable`。
- `BatchResumeToken` 只用于恢复 target set 的 runtime position，不承载 scheduler、业务优先级、运营策略或 provider fallback。
- 初次执行中断并返回 `result_status=resumable` 时，`item_outcomes` 只包含已经处理完成的 target-set 前缀；未执行 item 不生成 pending/not_started outcome，调用方必须通过 `resume_token.next_item_index` 和原始 target set 判断剩余范围。
- 使用 resume token 发起恢复执行后，Core 必须返回新的 batch envelope；若恢复后完成，`item_outcomes` 必须包含完整 target set 的 canonical combined outcomes。若再次中断，`item_outcomes` 必须扩展为截至新 `next_item_index` 的已处理前缀。
- resume 后必须复用同一 `batch_id`、target set hash、dedup state、`dataset_id` 与 dataset sink state；已写入 dataset record 的 item 不得重复写入，已标记 `duplicate_skipped` 的 item 不得在恢复后变成 success write。
- 成功 item 可投影为 `DatasetRecord.normalized_payload`，同时保留 `source_operation`、`adapter_key`、`target_ref`、`raw_payload_ref`、`evidence_ref` 与 `dedup_key`。
- Dataset sink 必须支持 write、readback、audit replay 的最小 contract；首个实现只能使用 JSON-safe reference sink，不引入产品数据库 schema、storage handle 或内容库模型。
- `BatchItemOutcome` 必须复用已有 read-side operation result envelope；不得在 batch contract 中重新定义 creator/comment/media/content 的私有字段。
- item operation 需要资源时，仍由已有 resource governance 通过单 item execution path 处理；batch 本身不得要求真实账号、登录态或 resource bundle 作为 Core admission 前置条件。

## GWT 验收场景

### 场景 1：全部 item 成功

Given batch request 包含两个稳定 read-side target item
When Core 顺序执行每个 item
Then batch result 返回 `result_status=complete`，每个 `BatchItemOutcome` 为 `succeeded`，dataset sink 写入两条 dataset records

### 场景 2：部分成功保留 item-level failure

Given batch request 包含一个成功 item 与一个 `permission_denied` item
When Core 执行 batch
Then batch result 返回 `result_status=partial_success`，成功 item 保留 read-side success envelope，失败 item 保留 failure envelope，dataset sink 只写成功 item record

### 场景 3：全部失败

Given batch request 的所有 target item 都返回 fail-closed error
When Core 执行 batch
Then batch result 返回 `result_status=all_failed`，每个 item outcome 都包含 item-level error，dataset sink 不写 success record

### 场景 4：duplicate target first-wins

Given batch request 包含两个相同 `dedup_key` 的 target item
When Core 执行 batch
Then 第一个 item 按正常路径处理，后续 duplicate item 返回 `duplicate_skipped`，dataset sink 不写第二份 record；若没有失败或中断，batch result 返回 `result_status=complete`

### 场景 5：resume token 只恢复 runtime position

Given batch execution 在第 N 个 item 后中断，并生成 resume token
When Core 返回 interrupted envelope
Then 该 envelope 的 `result_status=resumable`，且只包含前 N 个已处理 item 的 outcomes；token 不包含 scheduler rule、business priority、provider fallback 或 marketplace 信息

When caller 使用该 token 恢复同一 batch target set
Then Core 从 recorded runtime position 继续执行，并在恢复完成时返回包含完整 target set canonical outcomes 的 terminal envelope；dataset dedup/write state 不重复写入已完成 item

### 场景 6：dataset record 可回读和审计

Given batch 成功写入 dataset records
When consumer 按 dataset id 或 batch id 回读
Then 返回 JSON-safe `DatasetRecord`，包含 `source_operation`、脱敏 `adapter_key`、`target_ref`、`raw_payload_ref`、`normalized_payload`、`evidence_ref`、`source_trace`、`dedup_key`、`batch_id` 与 `batch_item_id`

### 场景 7：dataset replay 不需要 raw payload files

Given dataset audit replay 读取已写入 records
When replay 输出审计视图
Then replay 使用 sanitized evidence alias 与 normalized payload，不需要 raw payload files、storage handles、本地路径或 source names

### 场景 8：item resource requirement 仍走既有 resource governance

Given 某个 item operation 需要 account/proxy resource profile
When batch 执行该 item
Then Core 通过既有单 item resource governance 路径处理 acquire/release/failure；batch request 本身不要求真实账号或登录态作为 admission 前置条件

### 场景 9：read-side envelope 不被 batch 重写

Given batch item operation 是 `comment_collection` 或 `media_asset_fetch_by_ref`
When Core 生成 item outcome 与 dataset record
Then Core 只封装已有 public result envelope，不重新定义 comment hierarchy、creator profile、media metadata 或 content item 私有字段

### 场景 10：sanitized evidence enforcement

Given batch audit trace 或 dataset record 尝试写入 source name、本地路径、storage handle、private account/media/creator field 或 raw payload inline
When validator 检查 carrier
Then carrier 必须 fail-closed，并返回 contract validation error

## 异常与边界场景

- invalid target item operation 不属于稳定 read-side operations 时，batch request 必须被拒绝。
- resume token 绑定的 `batch_id`、target set hash 或 next item position 不一致时，必须返回 invalid/expired resume boundary。
- dataset sink write 失败时，item outcome 不得伪装为 dataset-written success；batch result 必须保留 dataset write failure audit。
- dataset record 的 `normalized_payload` 必须是 JSON-safe value；不可序列化对象必须 fail-closed。
- duplicate detection 只能基于 contract-level `dedup_key`，不得依赖平台私有 raw id。
- batch audit trace 不得记录 provider selector、fallback、marketplace 或 routing policy。
- `adapter_key` 与 `source_trace` 只能使用 Syvert 内部脱敏 alias；不得写入平台 source name、外部项目名、provider path、账号池、代理池、本地路径或 storage handle。

## 验收标准

- [ ] formal spec 冻结 batch request / target set、item outcome、partial success/failure、resume token 与 audit trace。
- [ ] formal spec 冻结 dataset record / sink 最小模型、readback 与 audit replay。
- [ ] formal spec 明确 item outcome 复用 read-side result envelope，不重写实体字段。
- [ ] formal spec 明确 resource governance 是 item-operation-scoped，batch 本身没有真实账号前置条件。
- [ ] formal spec 明确 scheduler、write-side、content library、BI、UI、provider selector/fallback/marketplace 均不在范围内。
- [ ] release `v1.6.0` 只作为显式 planning / closeout decision 绑定，不从 `#382` 或 roadmap title 推导。
