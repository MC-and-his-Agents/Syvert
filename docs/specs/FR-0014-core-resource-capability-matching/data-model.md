# FR-0014 数据模型

## 实体清单

- 实体：`ResourceCapabilityMatcherInput`
  - 用途：表达 Core 在调用 runtime matcher 前需要提供的 canonical 输入上下文
- 实体：`ResourceCapabilityMatchResult`
  - 用途：表达 matcher 对当前能力集合是否满足声明的 canonical 结论

## 关键字段

- `ResourceCapabilityMatcherInput`
  - `task_id`
    - 约束：非空字符串；matcher 必须在 task-bound 上下文中工作
  - `adapter_key`
    - 约束：非空字符串；必须与 `requirement_declaration.adapter_key` 一致
  - `capability`
    - 约束：非空字符串；必须与 `requirement_declaration.capability` 一致
  - `requirement_declaration`
    - 约束：必须满足 `FR-0013` 的 `AdapterResourceRequirementDeclaration` contract；不得使用影子声明 carrier
  - `available_resource_capabilities`
    - 约束：去重集合；元素必须全部来自 `FR-0015` 已批准词汇；当前只允许 `account`、`proxy`
    - 允许值：空集合是合法输入，但若声明要求必需能力，它只能导向 `unmatched`
- `ResourceCapabilityMatchResult`
  - `task_id`
    - 约束：非空字符串；必须与 matcher input 保持一致
  - `adapter_key`
    - 约束：非空字符串；必须与 matcher input 保持一致
  - `capability`
    - 约束：非空字符串；必须与 matcher input 保持一致
  - `match_status`
    - 约束：只允许 `matched`、`unmatched`
    - 语义：
      - `matched`：当前能力集合满足全部 `required_capabilities`
      - `unmatched`：当前能力集合无法满足全部 `required_capabilities`

## 匹配规则

- 输入前置校验：
  - 若 `requirement_declaration` 非法，或 `available_resource_capabilities` 出现未批准能力标识，则不返回 `ResourceCapabilityMatchResult`，而是按 `runtime_contract + invalid_resource_requirement` fail-closed
  - 若 `task_id / adapter_key / capability` 与 `requirement_declaration` 上下文不一致，也必须走 `invalid_resource_requirement`
- 结论规则：
  - `resource_dependency_mode=none` 且 `required_capabilities=[]` -> `matched`
  - `resource_dependency_mode=required` 且 `required_capabilities` 为 `available_resource_capabilities` 的子集 -> `matched`
  - `resource_dependency_mode=required` 且 `required_capabilities` 不是其子集 -> `unmatched`
- 明确禁止：
  - partial match
  - 排序、打分、偏好、fallback
  - provider 选择或资源实例绑定

## 错误口径投影

- `invalid_resource_requirement`
  - 触发条件：
    - matcher 输入形状非法
    - 声明形状非法
    - 出现未批准能力标识
    - 上下文字段与声明不一致
  - 错误分类：`runtime_contract`
- `resource_unavailable`
  - 触发条件：
    - matcher 输入合法，且声明也合法，但 `match_status=unmatched`
  - 错误分类：沿用现有 shared runtime 的 `runtime_contract` 口径，不重新命名

## 生命周期

- 创建：
  - 当 Core 在调用 adapter 前需要验证资源能力是否满足声明时，创建 `ResourceCapabilityMatcherInput`
- 更新：
  - matcher 对同一输入只允许产出一个 `ResourceCapabilityMatchResult`
  - 任何导致 partial match、排序或 provider 选择的中间态都不属于本 FR 的 canonical 数据模型
- 失效/归档：
  - 本 FR 不定义 matcher trace、缓存或历史审计 schema；如需新增，必须通过新的 formal spec 冻结
