# FR-0004 数据模型

本文件只定义 `FR-0004` 引入的共享模型语义，不定义实现代码、持久化表结构或资源对象模型。

## `InputTarget`

### 角色

- 表示调用侧“采什么”的共享输入模型。
- 由 Core 在请求受理阶段消费，并在进入 adapter 前完成投影。

### 最小字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `adapter_key` | `string` | Core 侧路由标识；不要求进入 adapter-facing request |
| `capability` | `string` | 调用侧 operation 标识 |
| `target_type` | `string` | `target_value` 的解释方式 |
| `target_value` | `string` | 调用方显式提供的目标值 |

### 约束

- 四个字段都必须存在，且值不能为空字符串。
- `target_type` 当前最小允许值为：`url`、`content_id`、`creator_id`、`keyword`。
- 平台主 ID、签名参数、cookie、headers、页面态线索都不属于本模型。

## `CollectionPolicy`

### 角色

- 表示调用侧“在什么约束下采”的共享策略模型。
- 由 Core 在共享输入层消费，用于约束 admission 与后续投影语义。

### 最小字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `collection_mode` | `string` | 采集策略轴 |

### 约束

- `collection_mode` 当前最小允许值为：`public`、`authenticated`、`hybrid`。
- 本 FR 只冻结策略语义，不冻结资源对象结构或资源可用性判定算法。

## `FR-0002` 兼容投影

| 旧输入 | 新模型投影 |
| --- | --- |
| `adapter_key` | `InputTarget.adapter_key` |
| `capability=content_detail_by_url` | 调用侧 operation id，后续投影为 adapter-facing capability family `content_detail` |
| `input.url` | `InputTarget.target_type=url` + `InputTarget.target_value=input.url` |
| 缺失策略字段 | `CollectionPolicy.collection_mode=hybrid` |

### 兼容特例

- 对上述 legacy `hybrid` 投影，若 adapter 只声明 `public` 或只声明 `authenticated`，Core 仍可把该请求视为合法承接目标。
- 该特例只服务 `FR-0002` 的兼容投影，不自动推广到 native `FR-0004` 调用方显式提交的 `hybrid` 请求。
