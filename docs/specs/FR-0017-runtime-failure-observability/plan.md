# FR-0017 实施计划

## 关联信息

- item_key：`FR-0017-runtime-failure-observability`
- Issue：`#220`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 exec-plan：
  - `docs/exec-plans/FR-0017-runtime-failure-observability.md`
  - `docs/exec-plans/CHORE-0150-fr-0017-formal-spec-closeout.md`

## 实施目标

- 在进入 runtime implementation 前，冻结运行时失败可观测性的最小 formal contract：失败分类投影、结构化日志、最小执行指标，以及它们与 `task_id`、TaskRecord、failed envelope、resource trace、`FR-0016` 的 `ExecutionAttemptOutcome` / `ExecutionControlEvent` 的关联规则。

## 分阶段拆分

- 阶段 1：`#226` 收口 formal spec，建立 `spec.md`、`plan.md`、`risks.md`、`data-model.md`、`contracts/README.md` 与两个 exec-plan，只提交文档规约。
- 阶段 2：`spec review` 通过后，进入 `#227` runtime implementation，由独立 implementation PR 落地 failure signal、structured log 与 minimal metrics，不在本 PR 中修改 `syvert/**`、`tests/**`、`scripts/**`。
- 阶段 3：`#227` 通过实现审查与门禁后，由 `#228` parent closeout 收口 FR-0017 的 GitHub 状态、repo semantic truth、PR 状态、验证证据与主干一致性。

## 实现约束

- 不允许触碰的边界：
  - 不得在本事项中实现 runtime、测试或脚本改造
  - 不得重写 `FR-0005` 错误分类或新增 observability 私有错误分类
  - 不得重写 `FR-0008` TaskRecord 状态机、终态 envelope 或持久化语义
  - 不得重写 `FR-0011` ResourceTraceEvent 或资源状态机
  - 不得重写 `FR-0016` timeout / retry / concurrency 策略
  - 不得放宽 `FR-0016` 固定 retryable predicate、正常 timeout 分类，或 accepted 前后 concurrency rejection 边界
  - 不得创建 release / sprint 索引
- 与上位文档的一致性约束：
  - 与 `AGENTS.md` 对“Core 负责运行时语义、Adapter 负责目标系统语义”的规则保持一致
  - 与 `WORKFLOW.md` 对“Work Item 是执行入口、formal spec 绑定 FR、repo 是语义真相”的规则保持一致
  - 与 `spec_review.md` 对 formal spec 最小套件、GWT、风险、contract / data model 的审查要求保持一致

## 测试与验证策略

- formal spec 阶段：
  - `python3 scripts/spec_guard.py --mode ci --all`
  - `python3 scripts/docs_guard.py --mode ci`
  - `python3 scripts/workflow_guard.py --mode ci`
- implementation 阶段：
  - unit tests：验证 `RuntimeFailureSignal` 从 failed envelope 投影 `error_category / error_code`，并拒绝分类漂移
  - contract tests：验证结构化日志、指标与 failure signal 共享 `task_id`，并能关联 TaskRecord / envelope / resource trace / `ExecutionAttemptOutcome` / `ExecutionControlEvent`
  - runtime tests：覆盖正常 `execution_timeout -> platform + error.details.control_code=execution_timeout`、closeout/control-state failure -> `runtime_contract`、命中固定 retryable predicate 才允许 `retry_scheduled`、pre-accepted `admission_concurrency_rejected`、post-accepted `retry_concurrency_rejected`、resource acquire 后 adapter failure、observability write failure 的最小分支
- 手动验证：
  - 核对文档没有引入完整 observability 平台、采集后端、指标存储或 dashboard
  - 核对 success envelope 的 `raw` / `normalized` 未被本 FR 改写
  - 核对 `#227` 和 `#228` 的后续关系已在 plan 中写清

## TDD 范围

- 先写测试的模块：
  - 本事项为 formal spec closeout，不涉及运行时代码或测试文件变更
  - `#227` runtime implementation 必须先补 failure signal projection、structured log schema、minimal metrics 与 `ExecutionAttemptOutcome` / `ExecutionControlEvent` 投影相关测试
- 暂不纳入 TDD 的模块与理由：
  - 日志采集后端、指标存储、dashboard、observability 平台集成不属于 `v0.6.0` 本 FR 范围

## 并行 / 串行关系

- 可并行项：
  - `#226` 与其他 `v0.6.0` spec Work Item 可并行起草，只要写集分离且不改写相邻 FR
  - `#223 / #229 / #233` 可在各自 ownership 内并行推进，不应修改本 FR 的授权路径
- 串行依赖项：
  - `#227` runtime implementation 必须等待本 formal spec 通过 `spec review`
  - `#228` parent closeout 必须等待 `#227` implementation 完成、审查通过并与主干真相一致
- 阻塞项：
  - 若失败分类投影没有先冻结，runtime implementation 会把 timeout / retry / concurrency 误写成新的错误分类
  - 若 TaskRecord / envelope / resource trace / runtime result carrier 的关联规则没有先冻结，后续失败排查会继续依赖不可审查的私有日志
  - 若 accepted 前后的 concurrency rejection 不拆开，runtime implementation 会把 post-accepted retry reacquire rejection 错投为 admission rejection，或错误改写最终 failed envelope 的顶层 `error_code / error_category`

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] `RuntimeFailureSignal`、`RuntimeStructuredLogEvent`、`RuntimeExecutionMetricSample` 的最小字段与关联规则已冻结
- [ ] 正常 `execution_timeout` 与 closeout/control-state failure 的 observability 投影已按 `platform` / `runtime_contract` 分界冻结
- [ ] `admission_concurrency_rejected` 与 `retry_concurrency_rejected` 的日志/指标区分及 envelope 投影边界已冻结
- [ ] 已明确 `#227` 是 runtime implementation 入口，`#228` 是 parent closeout 入口
- [ ] 当前 formal spec PR 未混入实现代码、脚本、测试或 release / sprint 索引
