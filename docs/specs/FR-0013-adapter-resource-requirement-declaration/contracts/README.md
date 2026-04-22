# FR-0013 Contracts README

## Canonical Carrier

- `AdapterResourceRequirementDeclaration`
  - 用途：表达 adapter-facing capability 对共享受管资源能力的最小声明
  - 顶层字段固定为：
    - `adapter_key`
    - `capability`
    - `resource_dependency_mode`
    - `required_capabilities`
    - `evidence_refs`

## Field Contract

- `adapter_key`
  - 必须是非空字符串
- `capability`
  - 必须是非空字符串
  - 当前 formal contract 只允许 `content_detail`
- `resource_dependency_mode`
  - 只允许：`none`、`required`
- `required_capabilities[]`
  - `resource_dependency_mode=none`
    - 必须是空数组 `[]`
  - `resource_dependency_mode=required`
    - 必须是非空、去重数组
    - 值只允许：`account`、`proxy`
- `evidence_refs[]`
  - 必须是非空、去重字符串数组
  - 每个成员都必须绑定到 `FR-0015` 已批准共享证据

## Allowed Baseline Declarations

- 当前双参考适配器共享声明基线：
  - `xhs + content_detail -> required [account, proxy]`
  - `douyin + content_detail -> required [account, proxy]`
- carrier 仍必须允许 `none`
  - 语义：该 capability 当前不依赖共享受管资源
  - 约束：`required_capabilities=[]`

## Forbidden Surface

以下字段或语义不得进入 `AdapterResourceRequirementDeclaration`：

- `preferred_capabilities`
- `optional_capabilities`
- `fallback`
- `priority`
- `provider_selection`
- Playwright
- CDP
- Chromium
- browser provider
- sign service
- 任何平台私有 token / 签名 / 指纹字段

## Fail-Closed Cases

以下情况都必须视为 contract violation：

- 缺少任一固定字段
- `resource_dependency_mode` 不在 `none|required` 范围内
- `resource_dependency_mode=none` 但 `required_capabilities[]` 非空
- `resource_dependency_mode=required` 但 `required_capabilities[]` 为空、重复或带有未知值
- `evidence_refs[]` 为空、重复、形状不合法，或无法证明其来自 `FR-0015` 共享证据
