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

- declaration 至少包含一个 profile
- profile `profile_key` 在 declaration 内必须唯一
- `resource_dependency_mode=none` -> `required_capabilities=[]`
- `resource_dependency_mode=required` -> `required_capabilities` 非空、去重，且只能来自 `account`、`proxy`
- `evidence_refs` 非空、去重，并且每个引用都必须回指 `FR-0015` approved shared profile evidence
- 同一 declaration 内不得出现语义重复 profile

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
- 外部失败 envelope 对合法未命中路径继续使用 `resource_unavailable`

## explicitly forbidden

- `priority`
- `fallback`
- `preferred_profiles`
- `optional_capabilities`
- `provider_selection`
- `provider_offer`
- Playwright / CDP / Chromium / browser profile / network tier 技术字段
