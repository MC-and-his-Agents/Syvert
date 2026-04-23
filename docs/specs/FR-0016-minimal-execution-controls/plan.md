# FR-0016 实施计划

## 关联信息

- item_key：`FR-0016-minimal-execution-controls`
- Issue：`#219`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 exec-plan：`docs/exec-plans/CHORE-0147-fr-0016-formal-spec-closeout.md`

## 实施目标

- 为 `v0.6.0` 冻结 Core 最小执行控制 contract，明确 timeout、retry、concurrency 的 shared runtime 语义、错误投影、TaskRecord 影响和后续实现边界。
- 让后续 `#224` 可以在不重写 requirement 的前提下实现 Core timeout / retry / concurrency，并为 `FR-0017`、`FR-0018`、`FR-0019` 提供稳定输入。

## 分阶段拆分

- 阶段 1：建立 `FR-0016` formal spec 套件，冻结 `ExecutionControlPolicy`、attempt timeout、basic retry 与 fail-fast concurrency gate。
- 阶段 2：补齐 data model、contracts 摘要与风险清单，明确 TaskRecord、failed envelope、resource release 与 late completion 的边界。
- 阶段 3：通过 `#223` 独立 spec PR 完成 formal spec review、guardian、checks 与 squash merge，使 `FR-0016` 成为 implementation-ready requirement input。
- 阶段 4：在后续 `#224` implementation Work Item 中实现 Core runtime，不在当前 spec PR 中修改 `syvert/**`、`tests/**` 或 HTTP API。
- 阶段 5：由 `#225` parent closeout 对齐 spec、实现、验证证据、GitHub 状态与主干事实。

## 实现约束

- 不允许触碰的边界：
  - `#223` 只允许修改 `docs/specs/FR-0016-minimal-execution-controls/` 与 `docs/exec-plans/FR-0016-minimal-execution-controls.md`、`docs/exec-plans/CHORE-0147-fr-0016-formal-spec-closeout.md`
  - 不修改 `syvert/**`、`tests/**`、`scripts/**`、`.github/**`
  - 不实现 HTTP API、后台队列、生产调度器或 release gate runtime
  - 不改写 `FR-0005` 错误分类闭集、`FR-0008` TaskRecord 主状态机或 `FR-0010` 到 `FR-0015` 资源能力 contract
- 与上位文档的一致性约束：
  - 与 `#218` 的 `v0.6.0` 最小可运维目标保持一致
  - 与 `AGENTS.md` / `WORKFLOW.md` 的 formal spec 与实现分离规则保持一致
  - 与 `spec_review.md` 的 GWT、异常、验收、风险、TDD 与进入实现条件保持一致

## 测试与验证策略

- 单元测试：
  - 当前 formal spec PR 不引入单元测试；`#224` 需要补 runtime policy validation、timeout、retry 与 concurrency gate 单测
- 集成/契约测试：
  - 当前 PR 运行 `python3 scripts/spec_guard.py --mode ci --all`
  - 当前 PR 运行 `python3 scripts/docs_guard.py --mode ci`
  - 当前 PR 运行 `python3 scripts/workflow_guard.py --mode ci`
  - 当前 PR 运行 `python3 scripts/governance_gate.py --mode ci --base-sha <merge-base> --head-sha <head> --head-ref issue-223-fr-0016-formal-spec`
- 手动验证：
  - 按 `spec_review.md` rubric 核对 timeout、retry、concurrency 的目标边界、异常场景、TaskRecord 影响与 implementation-ready 条件
  - 核对 `#219` / `#223` 的 issue context 与 PR carrier 一致

## TDD 范围

- 先写测试的模块：
  - `#224` implementation 需要先写 policy validation、attempt timeout、retry attempt sequencing、concurrency rejection、late completion protection 与 TaskRecord 终态一致性测试
- 暂不纳入 TDD 的模块与理由：
  - 当前 `#223` 只冻结 formal spec，不实现 runtime
  - HTTP endpoint、CLI/API same-path regression 与 v0.6 release gate 分别属于 `FR-0018` / `FR-0019` 后续 Work Item

## 并行 / 串行关系

- 可并行项：
  - `FR-0016` spec、data model、contracts、risks 与 exec-plan 起草可以并行
  - `FR-0017` formal spec 可在消费本 FR 控制 outcome 的前提下并行准备，但不得反向改写本 FR 的 control policy
- 串行依赖项：
  - `#224` runtime implementation 必须在 `#223` formal spec review 通过并合入后开始
  - `FR-0018` HTTP API 不得在未消费本 FR Core execution control path 的情况下宣称同路径
  - `FR-0019` gate matrix 必须覆盖本 FR 批准的 timeout、retry 与 concurrency 场景
- 阻塞项：
  - 若 `ExecutionControlPolicy`、retryable scope 或 concurrency fail-fast 语义未冻结，`#224` 不应进入实现
  - 若 spec review 要求重开 TaskRecord 状态机或错误分类闭集，必须先回到对应上游 FR，而不是在本 FR 私自扩张

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] `ExecutionControlPolicy`、timeout、retry、concurrency 的字段与值域已冻结
- [ ] retryable outcome、concurrency reject、late completion 与资源释放边界已冻结
- [ ] `#224` 的 TDD 范围、回归证据与不纳入项已明确
