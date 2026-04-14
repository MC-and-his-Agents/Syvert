# Syvert 实现 PR 审查标准

本文档定义实现 PR 的工件完整性检查、review rubric、审查结论与 merge gate。

## 审查输入

审查输入遵循“最小必要上下文”原则：只对齐支撑当前事项、当前 diff、当前 `head SHA` 判断所必需的输入类别，不默认要求 reviewer 重复探索整仓历史。

默认优先对齐：

- 当前 PR 的标题、描述、风险、验证、回滚与事项上下文
- 与当前事项直接相关的 `spec` / `plan` / bootstrap contract / `exec-plan`
- 与当前改动直接相关的治理或流程文档
- 当前 diff、受影响文件与必要的调用链 / contract 边界
- 若事项声明 `integration_touchpoint != none`，补充对应的 `integration_ref` 及其当前依赖 / 联合验收状态
- 若需要引用 owner project / labels / issue backfill，只能把它们当作 rollout evidence；reviewer 不得把 evidence 文档当作 `integration_ref` 当前状态的替代品

仅当历史事项确有 legacy `TODO.md`，且其中内容对当前风险、恢复或历史判断直接相关时，才补充该文件作为审查输入。

仅在当前阻断项需要更多证据、或上述输入无法支撑结论时，再补充：

- [AGENTS.md](./AGENTS.md)
- [WORKFLOW.md](./WORKFLOW.md)
- [docs/AGENTS.md](./docs/AGENTS.md)
- [docs/process/delivery-funnel.md](./docs/process/delivery-funnel.md)
- [docs/process/agent-loop.md](./docs/process/agent-loop.md)
- [docs/process/worktree-lifecycle.md](./docs/process/worktree-lifecycle.md)

若现有输入已足以判断，不应把上述文档清单整段视为每次审查都必须重新阅读的固定前置步骤，也不应把它们整段再次注入 reviewer prompt。

## 工件完整性检查

工件完整性检查只回答“当前 PR 是否具备进入审查的最小输入”，不等于 `APPROVE`。

至少确认：

- PR 范围、Issue、事项上下文与标题语义可映射
- 对应 `spec` / bootstrap contract / `exec-plan` 可定位
- 风险、验证、回滚信息已提供
- 需要的测试或验证证据已附上入口
- 受影响的 contract、数据模型、迁移说明在相关工件中可追溯

缺少上述输入时，reviewer 应先要求补齐工件，再继续实质审查。

## Review Rubric

优先检查阻断项，再看非阻断优化项。以下 rubric 回答“该实现是否满足 spec 并可安全进入 merge gate”，不是风格清单。

| 维度 | 审查重点 | 通过信号 | 典型阻断 |
| --- | --- | --- | --- |
| 与 spec / contract 一致性 | 实现是否忠实落实正式规约、contract、bootstrap contract | 行为、字段、边界、回滚约束与输入工件一致 | 私自改语义、实现与 contract 漂移、未回写规约变更 |
| 行为正确性 | 主流程、异常分支、边界条件是否按预期工作 | 关键路径有明确验证证据，失败模式与预期一致 | happy path 通过但异常/边界行为错误 |
| 回归风险 | 现有行为、兼容性、调用方假设是否被破坏 | 影响面说明清楚，回归点有针对性验证 | 修改共享路径却没有回归验证或兼容说明 |
| 测试有效性 | 测试是否真正覆盖风险，而非只增加表面覆盖率 | 测试命中关键分支、失败模式和回归点，断言与行为相关 | 测试只覆盖 mock/happy path，无法捕捉真实回归 |
| 错误处理与恢复 | 错误暴露、重试、降级、恢复路径是否清楚 | 错误能被观测、调用方可处理、恢复路径可验证 | 吞错、错误语义模糊、恢复路径未实现或不可验证 |
| 状态一致性 / 幂等 / 并发 | 状态迁移、重入、重复执行、并发访问是否安全 | 状态更新闭合，幂等/并发约束有实现与验证 | 写入竞态、重复执行副作用、状态机断裂 |
| 架构边界 | 是否遵守 Core / Adapter / governance / tool 的职责边界 | 改动位于正确层次，没有把平台语义泄漏到 Core | 为求快跨层耦合、边界破坏、临时逻辑常驻 |
| 复杂度与可维护性 | 实现是否足够简单、可读、可扩展 | 复杂度与问题规模匹配，抽象有明确收益 | 为小问题引入过度抽象，或堆叠难以维护的分支 |
| 可观测性 | 日志、指标、状态面、错误上下文是否足够定位问题 | 关键路径可定位，必要输出可支持发布后排障 | 出问题后无法判断输入、状态或失败原因 |
| 安全 / 性能 / 成本 | 是否引入安全缺口、性能回退、额外成本或配额风险 | 风险已评估并在必要处验证或约束 | 新增高耗时/高成本路径或安全暴露但无说明 |
| 发布与回滚准备 | 发布依赖、迁移步骤、回滚方式是否就绪 | 发布前提、回滚步骤、操作顺序清晰 | 需要人工操作却未记录，回滚方案缺失或不可执行 |
| integration 联动一致性 | 是否按 canonical integration contract 正确标记跨仓触点、依赖和联合验收约束 | PR 与 issue / work item 的 canonical integration 元数据一致，review packet 中可见 `integration_ref` 当前状态，且 reviewer 可确认提 PR 前检查口径成立 | 共享契约改动未标记 integration 联动、PR 与 issue canonical integration 漂移、跨仓事项缺少可核查的 integration 绑定，或 reviewer 看不到当前 `integration_ref` 状态 |

## 事项分级视角

- `轻量事项`：允许简化审查记录，但不能跳过门禁
- `中等事项`：必须证明范围与影响可控
- `核心事项`：必须绑定正式规约输入，且验证证据充分

## 审查结论

统一使用以下结论字段：

- `verdict`: `APPROVE` 或 `REQUEST_CHANGES`
- `safe_to_merge`: `true` 或 `false`

规则：

- 只要存在阻断项，`safe_to_merge` 必须为 `false`
- `REQUEST_CHANGES` 不得伴随 `safe_to_merge=true`
- reviewer 的结论来自 rubric 判断，不由工件完整性检查或 CI 结果自动推导

## 合并门禁

进入 `merge-ready` 前，必须同时满足：

1. 最新 guardian 结论为 `APPROVE`
2. guardian 结果 `safe_to_merge=true`
3. GitHub checks 全绿
4. PR 不是 Draft
5. 合并时 head 与审查时 head 一致
6. 必须通过受控入口 `merge_pr`
7. 若当前事项 `merge_gate=integration_check_required`，PR 描述必须补齐 canonical `integration_check`，且 merge-time integration recheck 只由 merge gate / guardian 消费，不要求 reviewer 先验完成
8. 若 review packet 无法读取 `integration_ref` 当前状态、依赖或联合验收结果，应按 fail-closed 处理，而不是用 rollout evidence 或 issue 摘录代替

merge gate 只回答“当前 PR 是否允许进入受控合并”，不替代 reviewer 对实现质量的实质判断。

受控 merge 入口应优先消费绑定当前 `head SHA` 的最新本地 guardian verdict；只有 verdict 缺失、已过期或 `head SHA` 已变化时，才补跑新的 guardian 审查。

## 合并方式

- 默认 Squash Merge
- 禁止把裸 `gh pr merge` 当作日常流程
- 合并动作应通过统一受控入口执行

## 职责边界说明

- `hook` 负责本地早反馈，不替代 CI
- `CI` 负责自动化校验，不替代 guardian
- `guardian` 负责合并前审查门禁
- reviewer rubric 负责识别语义正确性、风险与质量问题，不等于 merge gate
