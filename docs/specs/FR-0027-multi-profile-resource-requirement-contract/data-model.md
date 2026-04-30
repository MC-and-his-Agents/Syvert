# FR-0027 数据模型

## AdapterResourceRequirementDeclarationV2

- 作用：表达某个 `adapter_key + capability` 在 `v0.8.0` 下允许的 shared resource requirement profile 集合
- 字段：
  - `adapter_key`
    - 类型：`string`
    - 约束：非空；声明所属 adapter；每个 profile 引用到的 `ApprovedSharedResourceRequirementProfileEvidenceEntry.reference_adapters` 都必须覆盖该值
  - `capability`
    - 类型：`string`
    - 约束：非空；声明所属 adapter-facing capability
  - `resource_requirement_profiles`
    - 类型：`AdapterResourceRequirementProfile[]`
    - 约束：非空数组；每一项必须合法；同一 declaration 内不得出现语义重复 profile

## AdapterResourceRequirementProfile

- 作用：表达一个可被 matcher 独立判断的合法 shared profile
- 字段：
  - `profile_key`
    - 类型：`string`
    - 约束：声明内唯一、非空；只承担稳定标识职责
  - `resource_dependency_mode`
    - 类型：`enum`
    - 允许值：`none`、`required`
  - `required_capabilities`
    - 类型：`string[]`
    - 约束：
      - 当 mode=`none` 时必须为空数组
      - 当 mode=`required` 时必须非空、去重，且值只能来自 `account`、`proxy`
      - 比较、重复检测与 proof 对齐前，必须先按 `FR-0015` 已批准词汇顺序规范化；当前顺序固定为 `account`、`proxy`
  - `evidence_refs`
    - 类型：`string[]`
    - 约束：长度恰为 1、无重复；这唯一一个引用必须唯一命中一个在 `capability + execution_path + resource_dependency_mode + required_capabilities` 上与当前 profile 完全一致、且 `reference_adapters` 覆盖 declaration `adapter_key` 的 `ApprovedSharedResourceRequirementProfileEvidenceEntry.profile_ref`

## ApprovedSharedResourceRequirementProfileEvidenceEntry

- 作用：表达一个已被 `FR-0015` 证明为 shared、且可被 declaration / matcher / adapter migration 直接消费的 profile approval proof
- 字段：
  - `profile_ref`
    - 类型：`string`
    - 约束：非空、稳定、在当前 carrier 中唯一；是 declaration `evidence_refs` 的 canonical target
  - `capability`
    - 类型：`string`
    - 约束：当前只允许 `content_detail`
  - `execution_path`
    - 类型：`object`
    - 约束：
      - 保留与 `FR-0015` `ExecutionPathDescriptor` 等价的路径边界
      - 当前必须且只能表达 `operation=content_detail_by_url`、`target_type=url`、`collection_mode=hybrid`
  - `resource_dependency_mode`
    - 类型：`enum`
    - 允许值：`none`、`required`
  - `required_capabilities`
    - 类型：`string[]`
    - 约束：
      - 与被批准 profile 的 canonical tuple 完全一致
      - 当 mode=`none` 时必须为空数组
      - 当 mode=`required` 时必须非空、去重，且值只能来自 `account`、`proxy`
      - 比较与解析前必须先按 `FR-0015` 已批准词汇顺序规范化；当前顺序固定为 `account`、`proxy`
  - `reference_adapters`
    - 类型：`string[]`
    - 约束：当前必须且只能覆盖 `xhs`、`douyin`；任何消费该 entry 的 declaration 都必须满足 `adapter_key ∈ reference_adapters`
  - `shared_status`
    - 类型：`enum`
    - 允许值：沿用 `FR-0015` 既有词汇；当前 shared declaration 只接受 `shared`
  - `decision`
    - 类型：`enum`
    - 允许值：沿用 `FR-0015` 既有词汇；当前 shared declaration 只接受 `approve_for_v0_5_0`
  - `evidence_refs`
    - 类型：`string[]`
    - 约束：非空、去重；回指 `FR-0015` 中更细粒度的 research / artifact 证据

## ResourceCapabilityMatcherInputV2

- 作用：表达 matcher 的 canonical 输入
- 字段：
  - `task_id`
    - 类型：`string`
    - 约束：非空
  - `adapter_key`
    - 类型：`string`
    - 约束：必须与 declaration 一致
  - `capability`
    - 类型：`string`
    - 约束：必须与 declaration 一致
  - `requirement_declaration`
    - 类型：`AdapterResourceRequirementDeclarationV2`
    - 约束：必须合法
  - `available_resource_capabilities`
    - 类型：`string[] | set[string]`
    - 约束：去重集合；元素只能来自 `FR-0015` 已批准词汇；非法或重复输入一律归类为 `invalid_resource_requirement`

## ResourceCapabilityMatchResultV2

- 作用：表达 matcher 的 canonical 输出
- 字段：
  - `task_id`
  - `adapter_key`
  - `capability`
  - `match_status`
    - 允许值：`matched`、`unmatched`

## 判定规则

- declaration 不合法 -> `runtime_contract + invalid_resource_requirement`
- declaration profile 无法唯一映射到在 `capability + execution_path + tuple + adapter_key` 上完全对齐的 `ApprovedSharedResourceRequirementProfileEvidenceEntry` -> `runtime_contract + invalid_resource_requirement`
- declaration `adapter_key` 不在被引用 entry 的 `reference_adapters` 中 -> `runtime_contract + invalid_resource_requirement`
- `available_resource_capabilities` 非法、重复或包含未知词汇 -> `runtime_contract + invalid_resource_requirement`
- declaration 合法且任一 profile 被满足 -> `match_status=matched`
- declaration 合法但全部 profile 未命中 -> `match_status=unmatched`
- `unmatched` 若向外映射失败 envelope，继续使用 `resource_unavailable`
