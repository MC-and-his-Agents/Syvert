# FR-0003 风险清单

## 风险项

| 风险 | 影响 | 缓解策略 | 回滚策略 |
| --- | --- | --- | --- |
| GitHub 与仓库仍保留并行分层口径 | formal spec、exec-plan、PR 与 release/sprint 的归属继续漂移 | 在权威治理文档、formal spec、decision 中统一收敛为 `Phase -> FR -> Work Item` 与“GitHub 调度层 / 仓内语义层” | 使用独立 revert PR 回退本轮治理文档与 formal spec，恢复到上一个稳定口径 |
| 把 release / sprint 重新解释为状态真相源 | 破坏 GitHub 单一调度层，导致仓内出现第二套状态源 | 在 release / sprint 索引和顶层治理文档中反复强调“执行上下文 / 索引，不是状态真相” | 回退新增索引语义与治理表述，只保留不与 GitHub 真相竞争的最小入口 |
| 把 Work Item 唯一执行入口写得不够明确 | 后续事项可能继续绕过 FR 或 Phase 边界直接执行，破坏 closeout 语义 | 在 `WORKFLOW.md`、`delivery-funnel.md`、`agent-loop.md`、`exec-plan` 中重复固定该规则 | 回退有歧义的文档改动，并在下一轮治理中重新冻结唯一执行入口规则 |

## 合并前核对

- [x] 高风险项已有缓解策略
- [x] 回滚路径可执行
