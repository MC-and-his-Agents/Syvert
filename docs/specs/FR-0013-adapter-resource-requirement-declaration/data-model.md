# FR-0013 数据模型

## 实体清单

- 实体：`AdapterResourceRequirementDeclaration`
  - 用途：表达单个 adapter capability 对共享受管资源能力的最小声明

## 关键字段

- `AdapterResourceRequirementDeclaration`
  - `adapter_key`
    - 约束：非空字符串；绑定单一 adapter；不承载 provider / tenant / backend 选择语义
  - `capability`
    - 约束：非空字符串；当前只允许复用 adapter-facing 共享 capability `content_detail`
  - `resource_dependency_mode`
    - 约束：只允许 `none` 或 `required`
  - `required_capabilities`
    - 约束：数组；当 `resource_dependency_mode=none` 时必须为空数组
    - 约束：当 `resource_dependency_mode=required` 时必须为非空、去重数组
    - 约束：数组值只能来自 `FR-0015` 已批准共享词汇 `account`、`proxy`
    - 约束：不得承载 `preferred_capabilities`、`optional_capabilities`、`fallback`、`priority`、`provider_selection` 等扩张语义
  - `evidence_refs`
    - 约束：非空、去重字符串数组
    - 约束：每个成员都必须引用 `FR-0015` 已批准共享证据
    - 约束：不得引用本 FR 私有 research、临时实现注释、单平台实验材料或未审批的外部来源

## 生命周期

- 创建：
  - 当某个 adapter capability 的共享资源依赖已被 `FR-0015` 共享证据证明时，创建对应 `AdapterResourceRequirementDeclaration`
- 更新：
  - 只有在新的 formal spec 明确批准新增共享能力词汇、声明字段或证据绑定规则时，才能更新该 carrier；实现层不得私自追加字段
- 失效/归档：
  - 若某条声明被新 formal spec 替代，应通过新的 FR 或显式变更关闭旧语义；不得在实现层静默漂移
