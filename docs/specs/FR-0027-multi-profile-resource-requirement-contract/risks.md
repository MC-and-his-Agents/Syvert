# FR-0027 风险记录

| 风险 | 影响 | 缓解 | 回滚 |
| --- | --- | --- | --- |
| 多 profile 被误解释成优先级或自动 fallback | runtime 与 adapter 迁移会在 contract 外自行决定执行顺序，破坏 shared truth | formal spec 明确 `one-of legal profiles` 只表达合法集合，不表达顺序、偏好或自动回退 | 回滚相关字段与文案，恢复纯集合语义 |
| 未经 `FR-0015` 批准的 profile 被直接塞进 declaration | shared contract 被 adapter-local 宽松路径污染，后续开放接入 baseline 不可信 | declaration 强制绑定 profile-level evidence refs，未批准 profile 一律 fail-closed | 回滚违规 profile，并回到 evidence carrier 重新审查 |
| 新能力词汇借 multi-profile 模型偷渡进来 | `v0.8.0` 阶段边界失真，Core 抽象被过早扩张 | formal spec 限定 profile 组合空间只允许 `none/account/proxy` | 回滚越界能力，恢复最小组合空间 |
| 旧 `FR-0013/14/15` 被误当作仍然治理 `v0.8.0` multi-profile truth | reviewer、runtime 与 adapter migration 会同时消费两套冲突 contract | `FR-0027` 正文显式声明 version boundary，旧 FR 保留 `v0.5.0` 历史语义 | 在 closeout 中重新强调 governing artifact，并修正消费入口 |
| approval proof 不能唯一解析或 tuple identity 不稳定 | `#300/#301/#302` 会对同一 evidence_ref 解析出不同结论，formal contract 不可实现 | formal spec 明确 `profile_ref` 唯一、proof/declaration 共用同一 tuple canonicalization，并对 `required_capabilities` 固定规范化顺序 | 回滚歧义 proof carrier，恢复唯一解析规则 |
| declaration adapter 借用未覆盖自己的 shared proof | 未验证 adapter 可错误复用 `xhs/douyin` approved profile，破坏 fail-closed 边界 | formal spec 要求 proof `reference_adapters` 必须覆盖 declaration `adapter_key`，否则 `invalid_resource_requirement` | 回滚违规 binding，并在 evidence carrier 中重新声明合法覆盖面 |
| matcher 输入违法口径在 spec/data-model/contracts 间不一致 | `#301` 运行时实现可能把同一非法输入分别实现成 `unmatched` 或 `invalid_resource_requirement` | formal suite 明确：proof 不可解析、不唯一、不对齐、不覆盖 adapter，以及非法/重复/未知 `available_resource_capabilities` 一律 `invalid_resource_requirement` | 回滚漂移文案，重新对齐 formal suite 三个载体 |
| approved proof 丢失执行路径边界 | 同一 approved profile 会被无依据复用到其他 `content_detail` 路径，放宽证据适用面 | formal spec 保留等价于 `FR-0015` `ExecutionPathDescriptor` 的 proof path 约束，并把当前 approved slice 固定为 `content_detail_by_url + url + hybrid` | 回滚被放宽的 proof carrier，恢复路径绑定 |
| 把 profile approval 误写成 `v0.5.0` capability approval | `#300` 会被迫用错误词汇表达新的 profile truth，version boundary 失真 | formal spec 将 proof `decision` 明确建模为当前双参考 slice 的 profile-level approval，不再复用 `approve_for_v0_5_0` | 回滚错误词汇，恢复分层表达 |

## 检查清单

- [ ] formal spec 已明确 `one-of` 不是排序 / fallback
- [ ] formal spec 已明确 shared profile 必须回指 `FR-0015` approved evidence
- [ ] formal spec 已明确 `profile_ref` 唯一性、tuple canonicalization 与 adapter 覆盖规则
- [ ] formal spec 已明确 approved execution path 与 declaration-profile 单 proof 绑定规则
- [ ] formal spec 已明确非法 `available_resource_capabilities` 进入 `invalid_resource_requirement`
- [ ] formal spec 已明确当前不新增 `account` / `proxy` 之外的能力词汇
- [ ] formal spec 已明确 `FR-0027` 与 `FR-0013` / `FR-0014` / `FR-0015` 的版本化边界
