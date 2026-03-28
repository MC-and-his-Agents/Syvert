# FR-0001 风险记录

## 高风险项

### 1. guardian verdict 被错误复用

- 风险：如果 merge 入口消费了不受控来源的 guardian 结果，可能绕过真正的合并门禁。
- 缓解：
  - 只信任本地受控 state 中、绑定当前 `head SHA` 的 guardian 结果
  - 当结果缺失、过期或 `head SHA` 变化时，强制补跑 guardian 审查
  - 为 verdict 复用路径补充回归测试

### 2. merge gate 文档口径漂移

- 风险：高优先级文档的 merge gate 条件不一致，会导致人和 agent 无法一致判断 `merge-ready`。
- 缓解：
  - 高优先级文档统一引用 `code_review.md`
  - merge gate 的强条件只在 `code_review.md` 中完整定义

### 3. 核心治理事项缺少正式输入

- 风险：若治理基线调整没有对应 Issue 与 formal spec，后续审查无法证明范围、风险与验收边界。
- 缓解：
  - 为治理栈 v1 建立 Issue `#5`
  - 为当前事项补齐 `docs/specs/FR-0001-governance-stack-v1/`
  - 在 PR body 中显式关联 Issue 与 formal spec

## Stop-Ship 条件

- guardian 未给出 `APPROVE`
- `safe_to_merge=false`
- GitHub checks 未全绿
- PR `head SHA` 与最新 guardian 审查不一致

## 回滚策略

- 若治理栈合入后引发流程阻断或错误拒绝合并，通过独立 revert PR 回退本次治理栈改动。
