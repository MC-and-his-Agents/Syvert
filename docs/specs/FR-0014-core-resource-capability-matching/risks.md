# FR-0014 风险记录

| 风险 | 影响 | 缓解策略 | 回滚思路 |
| --- | --- | --- | --- |
| matcher 被扩张成 partial match / fallback 选择器 | Core 资源语义会从“满足性判断”漂移成调度策略层 | formal spec 明确只允许 `matched / unmatched` 两类结论，并禁止排序、偏好、fallback、provider 选择 | 回滚超范围字段与逻辑，恢复到纯集合满足性判断 |
| 合法声明被误报成 `invalid_resource_requirement` | runtime 无法区分“声明坏了”与“当前资源不足” | 明确把“合法声明但能力不足”固定映射到 `unmatched -> resource_unavailable` | 回滚错误分类逻辑，恢复 `invalid_resource_requirement` 只用于 contract 违法 |
| matcher 反向重写 `FR-0010` / `FR-0012` | bundle/lease 生命周期与注入边界会被 matcher 污染 | formal spec 明确 matcher 不定义 acquire / release、不定义注入责任 | 回滚跨 FR 语义，恢复相邻 FR 的 canonical truth |
| 未批准能力标识被 matcher 宽松接受 | `FR-0015` 的批准词汇边界会失效 | matcher 输入严格只接受 `FR-0015` 批准词汇，当前只允许 `account`、`proxy` | 回滚宽松输入，恢复 fail-closed 词汇校验 |
| 技术实现字段渗入 matcher input | 后续实现会被 Playwright / CDP / Chromium 等技术绑定锁死 | formal spec 明确禁止技术绑定字段进入 matcher surface | 回滚技术绑定输入，恢复实现无关 contract |

## 合并前核对

- [x] 高风险项已有缓解策略
- [x] `invalid_resource_requirement` 与 `resource_unavailable` 的口径边界已冻结
- [x] matcher scope 未扩张到 provider 选择或资源编排
