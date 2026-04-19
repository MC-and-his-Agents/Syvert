# FR-0010 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| 把部分 slot 成功也视为 acquire 成功 | Core 与 Adapter 对“是否拿到完整执行资源”产生分叉真相 | formal spec 明确 acquire 只能整包成功或整包失败 | 回滚实现，恢复为整包 fail-closed 语义 |
| 在 lifecycle 主 contract 中提前引入能力匹配或浏览器资源 | `v0.4.0` scope 漂移，后续 FR 边界失控 | 只冻结 `account` / `proxy` 与最小 slot 语义，其他能力留到后续 FR | 回滚超范围字段与规则，恢复到最小资源模型 |
| `release` 的幂等与冲突语义不明确 | 重试、补偿与失败恢复时可能重复回收或错误失效资源 | formal spec 明确“相同语义 no-op，冲突语义 fail-closed” | 回滚冲突 release 行为，恢复单一一致的 lease 收口规则 |
| `INVALID` 被实现层偷偷恢复为 `AVAILABLE` | 失效资源可能被再次注入执行路径，破坏最小安全边界 | formal spec 把 `INVALID` 定义为 `v0.4.0` 终态 | 回滚非法恢复路径，后续如需恢复机制则通过新 FR 显式引入 |

## 合并前核对

- [ ] 高风险项已有缓解策略
- [ ] acquire / release 的 fail-closed 行为已冻结
- [ ] `INVALID` 终态语义已冻结
