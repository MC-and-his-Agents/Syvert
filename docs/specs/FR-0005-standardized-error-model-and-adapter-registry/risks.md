# FR-0005 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| 把错误分类写得过细并绑定到当前代码结构 | 后续 `#69` 只能机械复制当前实现，失去在不改语义前提下重构的空间 | 只冻结分类边界、失败语义与 envelope 契约，不冻结类名、模块路径、异常继承关系 | 使用独立 revert PR 回退 `FR-0005` formal spec，并重新收敛分类边界 |
| 把 `unsupported`、`invalid_input`、`runtime_contract` 混写 | Core 无法稳定判断失败来源，harness 与 gate 也无法复用统一语义 | 在 `spec.md` 中显式拆开“请求不合法”“请求合法但不支持”“契约失配”三类失败 | 回退有歧义的 formal spec 修改，恢复到上一个清晰可判定的错误边界 |
| 把 registry discovery 写成真实平台副作用 | 后续 `FR-0006` 无法在不访问真实平台的前提下验证 contract | 在 spec 中固定 discovery 只消费稳定声明，不要求网络、登录态或浏览器副作用 | 回退 discovery 相关 formal spec，恢复到 side-effect-free 的最小契约 |
| formal spec 与 GitHub FR 状态失配 | 仓内已落地 formal spec，但 Issue 仍声明 `formal spec: 待创建`，导致真相不一致 | 在 merge 后同步更新 `#65` 的 formal spec 入口，并保持 Issue 继续作为未完结 requirement 容器 | 若同步失败，先保留 FR issue 为 OPEN，并补发 issue 更新或独立 docs-only 修正 |

## 合并前核对

- [x] 高风险项已有缓解策略
- [x] 回滚路径可执行
