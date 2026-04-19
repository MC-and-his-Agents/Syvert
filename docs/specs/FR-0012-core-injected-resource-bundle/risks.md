# FR-0012 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| Adapter 继续保留私有资源来源路径 | Core 无法成为资源运行时语义拥有者，平台泄漏检查失效 | formal spec 明确禁止 Adapter 自行来源化执行资源 | 回滚私有来源路径，恢复只能消费注入 bundle 的边界 |
| 注入 bundle 形状与 `FR-0010` 漂移 | lifecycle 主 contract 与调用边界出现两套 carrier | formal spec 明确 `resource_bundle` 复用 `FR-0010` canonical carrier | 回滚影子 bundle schema，恢复单一 bundle truth |
| Adapter 直接执行 release / invalidate | 资源状态与 tracing truth 可能被绕过 Core 私自改写 | formal spec 明确 Adapter 只能返回 disposition hint，最终收口由 Core 执行 | 回滚越权状态改写路径，恢复 Core 单一收口 |
| 缺 bundle 时继续调用 Adapter | Reference adapter 会自行补资源，破坏最小资源闭环 | formal spec 明确由 Core 在调用前 fail-closed | 回滚宽松 fallback，恢复前置校验 |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] `resource_bundle` 注入 carrier 与 `FR-0010` 一致
- [ ] Adapter 禁止自行来源化资源的边界已冻结
