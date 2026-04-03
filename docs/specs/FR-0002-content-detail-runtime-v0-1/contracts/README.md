# FR-0002 契约说明

## 接口名称与版本

- 接口名称：`content_detail_by_url`
- 版本语义：`v0.1.0` 最小业务 contract

## 输入结构

- `adapter_key`：显式指定执行该任务的 adapter
- `capability`：固定为 `content_detail_by_url`
- `input.url`：目标内容 URL

## 输出结构

- 成功态最小 envelope：
  - `task_id`
  - `adapter_key`
  - `capability`
  - `status`
  - `raw`
  - `normalized`
- 失败态最小 envelope：
  - `task_id`
  - `adapter_key`
  - `capability`
  - `status`
  - `error`

## 错误与边界行为

- Core 只处理运行时契约级错误，例如 adapter 不存在、capability 不受支持、成功结果缺失 `raw` 或 `normalized`。
- Adapter 处理平台级错误，例如 URL 无法解析、签名失效、未登录、验证码、内容不存在。
- `v0.1.0` 不要求统一的平台错误码体系，只要求失败 envelope 结构统一。

## 向后兼容约束

- 在 `v0.1.0` 范围内，`content_detail_by_url` 的最小输入字段和顶层结果 envelope 不得漂移。
- 若需要新增 Core 必需字段或修改 `normalized` 最小字段语义，必须回到 formal spec 审查链路。
