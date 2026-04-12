# FR-0004 风险记录

## 高风险项

### 1. 平台语义回流到 Core

- 风险：若 `InputTarget` 为了适配当前平台而吸收 `aweme_id`、`xsec_token`、签名字段或页面态线索，Core / Adapter 边界会再次漂移。
- 缓解：
  - formal spec 只冻结 `adapter_key`、`capability`、`target_type`、`target_value`
  - 明确 URL 派生值与平台主 ID 解析属于 adapter 内部职责

### 2. CollectionPolicy 退化为实现开关

- 风险：若把重试、速率、版本 gate、平台 fallback 或具体资源编排一并塞入 `CollectionPolicy`，该模型会吞并后续 FR 的职责。
- 缓解：
  - 当前 formal spec 只冻结 `collection_mode`
  - 其余执行策略轴必须在后续 FR 中单独建模并重新进入 spec review

### 3. 与 FR-0002 既有输入断裂

- 风险：若 `InputTarget` 无法无损表达 `adapter_key + capability + input.url`，后续实现会被迫引入破坏性迁移。
- 缓解：
  - formal spec 显式声明 `target_type=url` / `target_value=input.url` 的兼容映射
  - 当前 PR 不在实现层声称已完成运行时迁移

## Stop-Ship 条件

- formal spec 混入错误模型、adapter registry、fake adapter、harness、version gate 或实现代码
- `spec_guard` / `governance_gate` / `open_pr --dry-run` 任一失败
- guardian 未给出 `APPROVE` 或 `safe_to_merge=false`
- PR head 与最新 guardian 审查、checks 结果不一致

## 回滚策略

- 如需回滚，使用独立 revert PR 撤销 `FR-0004` formal spec 套件、最小 exec-plan 与 release / sprint 索引增量。
