# FR-0004 契约说明

本目录只记录 `FR-0004` 冻结的共享模型最小语义，不替代后续实现代码或测试夹具。

## `InputTarget`

- 角色：描述“采什么”
- 最小字段：
  - `adapter_key`
  - `capability`
  - `target_type`
  - `target_value`
- 共享语义：
  - `adapter_key` 绑定目标 adapter
  - `capability` 绑定请求的共享能力
  - `target_type` 说明 `target_value` 的解释方式
  - `target_value` 只承载调用方显式提供的目标值
- 不属于本模型的内容：
  - 平台主 ID 推导结果
  - 签名字段、cookie、headers、指纹或页面态 fallback 线索
  - 资源分配、重试、速率限制或版本 gate

## `CollectionPolicy`

- 角色：描述“在什么约束下采”
- 最小字段：
  - `collection_mode`
- 共享语义：
  - `public`：只能依赖公开访问路径
  - `authenticated`：必须依赖认证资源
  - `hybrid`：允许公开与认证两类合法路径并存
- 不属于本模型的内容：
  - 平台 fallback 选择器
  - 重试预算、分页、游标、结果范围
  - adapter registry、错误模型或 harness 协议

## 与 `FR-0002` 的兼容映射

- `adapter_key + capability + input.url`
- 等价映射为：
  - `adapter_key`
  - `capability`
  - `target_type=url`
  - `target_value=input.url`

## 后续 FR 的使用边界

- 错误模型、registry、fake adapter、harness、version gate 必须复用本目录定义的共享模型角色与边界。
- 若后续 FR 需要新增共享字段或改变取值语义，必须回到 formal spec 审查链路。
