# resource-capability-matcher contract（v0.5.0）

## 接口名称与版本

- 接口名称：`resource-capability-matcher`
- contract 版本：`v0.5.0`
- 作用：定义 Core 对资源能力集合进行前置满足性判断时的最小输入、输出与错误边界

## 输入结构

- `ResourceCapabilityMatcherInput`
  - 必填字段：
    - `task_id`
    - `adapter_key`
    - `capability`
    - `requirement_declaration`
    - `available_resource_capabilities`
  - 字段约束：
    - `task_id`：非空字符串
    - `adapter_key` / `capability`：必须与 `requirement_declaration` 同名字段一致
    - `requirement_declaration`：必须满足 `FR-0013` 已冻结 contract
    - `available_resource_capabilities`：去重集合；元素只能来自 `FR-0015` 已批准词汇，当前只允许 `account`、`proxy`

## 输出结构

- `ResourceCapabilityMatchResult`
  - 必填字段：
    - `task_id`
    - `adapter_key`
    - `capability`
    - `match_status`
  - 字段约束：
    - `match_status`：只允许 `matched`、`unmatched`
  - 输出边界：
    - 不返回 provider id
    - 不返回 resource_id
    - 不返回优先级、排序分数或 fallback 候选
    - 不返回 partial match carrier

## 匹配规则

- `resource_dependency_mode=none` 且 `required_capabilities=[]` -> `matched`
- `resource_dependency_mode=required` 时，只有在 `available_resource_capabilities` 覆盖全部 `required_capabilities` 时才允许 `matched`
- 只覆盖部分 `required_capabilities` 时必须返回 `unmatched`
- matcher 只判断“能力集合是否满足声明”，不选择 provider、不绑定资源实例，也不执行 acquire / release

## 错误与边界行为

- `invalid_resource_requirement`
  - 分类：`runtime_contract`
  - 适用场景：
    - `requirement_declaration` 形状非法
    - `requirement_declaration` 包含未批准能力标识
    - `available_resource_capabilities` 形状非法、重复或包含未批准能力标识
    - `task_id / adapter_key / capability` 与声明上下文不一致
- `resource_unavailable`
  - 适用场景：
    - matcher 输入合法
    - 声明合法
    - 但 `available_resource_capabilities` 无法覆盖全部 `required_capabilities`
  - 约束：
    - 这是合法声明下的资源不足口径，不得误报为 `invalid_resource_requirement`
- 禁止行为：
  - partial match
  - fallback / preferred / optional provider 推断
  - 排序、打分、优先级选择
  - Playwright / CDP / Chromium / browser profile 等技术绑定字段进入 matcher surface

## 向后兼容约束

- `FR-0014` 不改写 `FR-0010` 的 bundle / lease / slot lifecycle contract
- `FR-0014` 不改写 `FR-0012` 的 Core 注入 boundary
- 若未来需要 richer matching semantics，必须通过新的 formal spec 明确扩张，而不是在本 contract 中隐式追加字段或结论类型
