# FR-0027 风险记录

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| 多 profile 被误解释成优先级或自动 fallback | runtime 与 adapter 迁移会在 contract 外自行决定执行顺序，破坏 shared truth | formal spec 明确 `one-of legal profiles` 只表达合法集合，不表达顺序、偏好或自动回退 | 回滚相关字段与文案，恢复纯集合语义 |
| 未经 `FR-0015` 批准的 profile 被直接塞进 declaration | shared contract 被 adapter-local 宽松路径污染，后续开放接入 baseline 不可信 | declaration 强制绑定 profile-level evidence refs，未批准 profile 一律 fail-closed | 回滚违规 profile，并回到 evidence carrier 重新审查 |
| 新能力词汇借 multi-profile 模型偷渡进来 | `v0.8.0` 阶段边界失真，Core 抽象被过早扩张 | formal spec 限定 profile 组合空间只允许 `none/account/proxy` | 回滚越界能力，恢复最小组合空间 |
| 旧 `FR-0013/14/15` 被误当作仍然治理 `v0.8.0` multi-profile truth | reviewer、runtime 与 adapter migration 会同时消费两套冲突 contract | `FR-0027` 正文显式声明 supersede 边界，旧 FR 保留 `v0.5.0` 历史语义 | 在 closeout 中重新强调 governing artifact，并修正消费入口 |

## 检查清单

- [ ] formal spec 已明确 `one-of` 不是排序 / fallback
- [ ] formal spec 已明确 shared profile 必须回指 `FR-0015` approved evidence
- [ ] formal spec 已明确当前不新增 `account` / `proxy` 之外的能力词汇
- [ ] formal spec 已明确 `FR-0027` 与 `FR-0013` / `FR-0014` / `FR-0015` 的版本化边界
