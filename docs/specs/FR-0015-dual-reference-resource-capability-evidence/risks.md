# FR-0015 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| `#192/#193` 在上游词汇表冻结前各自发明能力标识 | `v0.5.0` 会出现影子抽象，需求声明与能力匹配无法围绕同一 contract 收敛 | formal spec 明确 `#192/#193` 只能消费 `managed_account / managed_proxy` | 回滚未批准的能力标识，恢复到 `FR-0015` 批准词汇表 |
| 单平台特例被误升格为共享能力 | Core 会长出平台特定抽象，破坏单一共享语义层 | 把单平台事实显式沉淀为 `adapter_only` 或 `rejected` 记录 | 回滚错误抽象，把相关信号退回 adapter 私有边界 |
| 共享词汇表绑定具体技术名词 | 后续 contract 被 Playwright/CDP/Chromium 等实现细节锁死 | formal spec 明确禁止技术名词进入共享能力标识 | 回滚技术特定命名，恢复语义级抽象 |
| evidence record 缺少可复验证据引用 | formal spec / review / implementation 会退化成口头判断 | 强制 `evidence_refs` 非空且可复验，并把 `#197` 绑定到同一 record contract | 回滚不完整记录，补齐证据后重新进入审查 |

## 合并前核对

- [x] 高风险项已有缓解策略
- [x] `#192/#193` 的上游消费边界已冻结
- [x] 单平台特例与 rejected candidate 的正式记录路径已冻结
