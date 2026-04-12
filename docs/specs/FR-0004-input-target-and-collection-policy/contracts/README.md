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
  - `adapter_key` 绑定目标 adapter 的 Core 侧路由输入
  - `capability` 绑定调用侧 operation 标识
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
  - `capability=content_detail_by_url`
  - `target_type=url`
  - `target_value=input.url`
  - `collection_mode=hybrid`

之所以固定为 `hybrid`，是因为 `FR-0002` 没有把“必须公开”或“必须认证”冻结为旧请求的一部分；若在兼容投影时擅自改成 `public` 或 `authenticated`，都会把既有单目标 URL 请求收窄为更强约束。

## 与 Adapter SDK 的关系

- `InputTarget` 与 `CollectionPolicy` 属于 Core 侧共享输入层。
- `adapter_key` 只承担 Core 路由语义，不要求进入 adapter-facing `AdapterRequest`。
- 对 `FR-0002` 的 `content_detail_by_url`，Core 在进入 adapter 前应完成如下投影：
  - 调用侧 operation id：`content_detail_by_url`
  - adapter-facing capability family：`content_detail`
  - `target_type=url`
  - `collection_mode=hybrid`；若目标 adapter 只声明单一模式，则在进入 adapter-facing request 前按其唯一声明模式归一化为 `public` 或 `authenticated`

## 后续 FR 的使用边界

- 错误模型、registry、fake adapter、harness、version gate 必须复用本目录定义的共享模型角色与边界。
- 若后续 FR 需要新增共享字段或改变取值语义，必须回到 formal spec 审查链路。
