# FR-0002 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| 把参考仓的一体化平台实现误当成 Syvert 架构蓝本 | Core/Adapter 边界被平台实现反向污染 | formal spec 中显式冻结 Core/Adapter 责任边界，研究结论只提炼平台事实 | 回退 spec 中超范围的架构或字段约束，回到最小 Core 契约 |
| 平台 detail URL、签名与登录态事实不清 | 适配器设计无法进入实现 | 先把未知项记录到 `research.md`，只冻结当前已知的最小 contract | 暂停实现 PR，补研究后重新发起 spec review |
| `normalized` 字段集过大或过小 | 过大导致平台泄漏，过小导致消费价值不足 | 只冻结双平台共同必需的最小字段，平台特有字段留在 `raw` | 回退字段集变更并重新评审 contract |
| 在 `v0.1.0` 过早引入 API、资源系统或调度能力 | 范围失控，偏离版本主轴 | spec 中显式列出不在范围项，review 时按阶段边界拦截 | 拆离超范围内容到后续事项，不在本 FR 中合入 |
| 仓内 formal spec 与 GitHub Issue / Project 状态失配 | 仓内进入 `implementation-ready`，但外部真相源未同步，导致执行优先级与关闭语义漂移 | 在 PR 描述与 spec review 结论中显式映射 `Issue #38`，并在进入 implementation 回合前同步更新外部状态 | 如回滚 formal spec PR，同时回收 `#38` 及 supporting issues `#39`-`#42` 的阶段/状态标记，确保 GitHub 仍是唯一 truth source |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] 回滚路径可执行
