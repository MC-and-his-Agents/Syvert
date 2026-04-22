# dual-reference-resource-capability-evidence contract（v0.5.0）

## 接口名称与版本

- 接口名称：`dual-reference-resource-capability-evidence`
- contract 版本：`v0.5.0`
- 作用：定义双参考适配器资源能力证据记录的最小 carrier、决策边界与批准词汇表

## 输入输出结构

- 输入结构：
  - 单条 `DualReferenceResourceCapabilityEvidenceRecord`
  - 固定字段：`adapter_key`、`capability`、`execution_path`、`resource_signals`、`candidate_abstract_capability`、`shared_status`、`evidence_refs`、`decision`
  - 当前共享 evidence baseline 约束：
    - `adapter_key` 只允许 `xhs`、`douyin`
    - `capability` 只允许 `content_detail_by_url`
    - `execution_path` 只允许 `hybrid_content_detail_by_url`
- 输出结构：
  - formal evidence truth：由单条或多条 `DualReferenceResourceCapabilityEvidenceRecord` 组成
  - approved vocabulary：当前只允许 `managed_account`、`managed_proxy`

## 错误与边界行为

- `invalid_input`
  - 适用场景：
    - 缺少任一固定字段
    - `shared_status` 不在 `shared / adapter_only / rejected` 内
    - `resource_signals` 或 `evidence_refs` 为空
    - `decision` 与 `shared_status` 不一致
- `runtime_contract`
  - 适用场景：
    - `shared_status=shared`，但 `candidate_abstract_capability` 不在 `managed_account / managed_proxy` 内
    - 证据记录试图把具体技术名词或单平台私有信号提升为共享资源能力
    - `#192/#193` 试图消费 `FR-0015` 未批准的能力标识
- 边界约束：
  - `adapter_only` 与 `rejected` 不是可忽略噪声，而是阻止错误抽象进入共享层的正式 evidence truth
  - 共享词汇表只冻结抽象能力标识与边界，不冻结 adapter 私有 material 字段命名
  - 证据不足时必须保持最小资源模型，而不是新增新的共享能力标识

## 向后兼容约束

- `adapter_key`、`capability` 继续复用上游已冻结的共享输入语义
- `v0.5.0` 的共享资源能力标识只允许 `managed_account` 与 `managed_proxy`
- 若未来要新增共享能力标识、execution path 或第三个平台，必须通过新的 formal spec 扩张 contract
