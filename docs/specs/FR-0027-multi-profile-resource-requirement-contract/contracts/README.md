# FR-0027 contracts

## declaration carrier

- canonical declaration：`AdapterResourceRequirementDeclarationV2`
- 目的：为同一 `adapter_key + capability` 声明多个都合法的 shared resource requirement profile

### required fields

- `adapter_key`
- `capability`
- `resource_requirement_profiles`

## profile carrier

- canonical profile：`AdapterResourceRequirementProfile`

### required fields

- `profile_key`
- `resource_dependency_mode`
- `required_capabilities`
- `evidence_refs`

### validation rules

- `adapter_key` 必须被每个被引用的 `ApprovedSharedResourceRequirementProfileEvidenceEntry.reference_adapters` 显式批准
- declaration 至少包含一个 profile
- profile `profile_key` 在 declaration 内必须唯一
- `resource_dependency_mode=none` -> `required_capabilities=[]`
- `resource_dependency_mode=required` -> `required_capabilities` 非空、去重，且只能来自 `account`、`proxy`
- `required_capabilities` 在重复检测、proof lookup 和 equality 判断前必须先按 `FR-0015` 已批准词汇顺序规范化；当前顺序固定为 `account`、`proxy`
- `evidence_refs` 长度恰为 1，并且这唯一一个引用都必须唯一命中一个在 `capability + execution_path + resource_dependency_mode + required_capabilities` 上与当前 profile 完全一致、且 `reference_adapters` 覆盖 declaration `adapter_key` 的 `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref`
- 同一 declaration 内不得出现语义重复 profile

## profile approval proof

- canonical consumer contract：`ApprovedSharedResourceRequirementProfileEvidenceEntry`

### required fields

- `profile_ref`
- `capability`
- `execution_path`
- `resource_dependency_mode`
- `required_capabilities`
- `reference_adapters`
- `shared_status`
- `decision`
- `evidence_refs`

### validation rules

- `profile_ref` 必须稳定、在当前 carrier 中唯一，且可被 declaration `evidence_refs` 精确引用
- `capability` 当前只允许 `content_detail`
- `execution_path` 必须保留与 `FR-0015` `ExecutionPathDescriptor` 等价的路径边界；当前只允许 `operation=content_detail_by_url`、`target_type=url`、`collection_mode=hybrid`
- `resource_dependency_mode=none` -> `required_capabilities=[]`
- `resource_dependency_mode=required` -> `required_capabilities` 非空、去重，且只能来自 `account`、`proxy`
- `resource_dependency_mode` / `required_capabilities` 必须与 declaration profile 的 canonical tuple 完全一致；比较前必须先按 `FR-0015` 已批准词汇顺序规范化
- `reference_adapters` 当前必须且只能覆盖 `xhs`、`douyin`
- 任何消费该 entry 的 declaration 都必须满足 `adapter_key ∈ reference_adapters`
- `shared_status` 沿用 `FR-0015` 既有词汇；当前 shared declaration 只接受 `shared`
- `decision` 沿用 `FR-0015` 既有词汇；当前 shared declaration 只接受 `approve_for_v0_5_0`
- `evidence_refs` 必须回指 `FR-0015` research / artifact 中更细粒度的双参考证据
- proof 不可解析、不唯一、不对齐、不在当前 approved execution path 内，或不覆盖 declaration adapter 时，一律归类为 `runtime_contract + invalid_resource_requirement`

## matcher contract

- input：`task_id`、`adapter_key`、`capability`、`requirement_declaration`、`available_resource_capabilities`
- output：`task_id`、`adapter_key`、`capability`、`match_status`

### allowed outputs

- `matched`
- `unmatched`

### matching rule

- 任一合法 profile 被满足 -> `matched`
- declaration 合法但全部 profile 未命中 -> `unmatched`
- declaration / profile / input 不合法 -> `runtime_contract + invalid_resource_requirement`
- `available_resource_capabilities` 非法、重复或包含未知词汇 -> `runtime_contract + invalid_resource_requirement`
- 外部失败 envelope 对合法未命中路径继续使用 `resource_unavailable`

## explicitly forbidden

- `priority`
- `fallback`
- `preferred_profiles`
- `optional_capabilities`
- `provider_selection`
- `provider_offer`
- Playwright / CDP / Chromium / browser profile / network tier 技术字段
