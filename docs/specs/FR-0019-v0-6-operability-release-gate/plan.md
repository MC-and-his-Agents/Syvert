# FR-0019 v0.6 operability release gate 实施计划

## 关联信息

- item_key：`FR-0019-v0-6-operability-release-gate`
- Issue：`#222`
- item_type：`FR`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 exec-plan：`docs/exec-plans/FR-0019-v0-6-operability-release-gate.md`、`docs/exec-plans/CHORE-0157-fr-0019-formal-spec-closeout.md`

## 实施目标

- 本次实施要交付的能力：冻结 `v0.6.0` operability release gate 与回归矩阵的 formal contract，使后续 `#234` 可以在不改写需求的前提下实现 timeout / retry / concurrency、failure / log / metrics、HTTP submit / status / result、CLI / API same-path 的门禁矩阵，并由 `#235` 完成 parent closeout。

## 规范性依赖同步

- `FR-0016`：后续实现必须按固定默认 policy 与 retry/concurrency 语义落地矩阵断言：
  - `timeout_ms=30000`
  - `retry.max_attempts=1`
  - `retry.backoff_ms=0`
  - `concurrency.scope=global`
  - `concurrency.max_in_flight=1`
  - `concurrency.on_limit=reject`
  - retryable predicate 只允许 `execution_timeout` 或 `platform+details.retryable=true` 的 transient failure（且通过 idempotency safety gate）
  - pre-accepted 并发拒绝：`invalid_input + 无 TaskRecord`
  - post-accepted retry reacquire 拒绝：只写 `ExecutionControlEvent.details`，不得改写上一 attempt 终态
- `FR-0017`：failure/log/metrics/refs 必须使用结构化字段；不得只做文本同义词对比。
- `FR-0018`：HTTP 与 CLI 必须共用 Core path；矩阵需断言同一 `TaskRecord` 与 shared envelope。

## 分阶段拆分

- 阶段 1：`#233` formal spec closeout。
  - 创建 `FR-0019-v0-6-operability-release-gate` formal spec 套件。
  - 明确承接 `FR-0007`，不重写旧 gate。
  - 明确不做 release closeout、tag、GitHub Release、外部 SaaS 监控、生产验收或分布式压测。
- 阶段 2：spec review。
  - 按 `spec_review.md` 审查目标边界、GWT、异常与边界、数据模型、contract 与风险。
  - spec review 通过后，`FR-0019` 才进入 implementation-ready。
- 阶段 3：`#234` release gate matrix implementation。
  - 实现 release gate matrix、case evidence、HTTP / CLI same-path 验证与本地可复验 logs / metrics 证据。
  - 不在 `#234` 中改写本 formal spec 的需求语义；若发现需求缺口，回到 spec review 链路。
- 阶段 4：`#235` parent closeout。
  - 汇总 `#233` spec、`#234` implementation、review、guardian、CI 与 GitHub 状态。
  - 只在满足 gate 与审查条件后收口父级状态；不由 `#233` 直接声明 release 完成。

## 实现约束

- 不允许触碰的边界：
  - `#233` 不修改 `syvert/**`、`tests/**`、`scripts/**`。
  - `#233` 不创建或更新 release / sprint 索引。
  - `#233` 不执行 release closeout、tag、GitHub Release 或主干合入。
  - 后续实现不得引入外部 SaaS 监控作为唯一证据，不得要求生产环境验收或分布式压测。
- 与上位文档的一致性约束：
  - 遵守 `AGENTS.md` 中 Core / Adapter 职责分离与 formal spec / 实现分离规则。
  - 遵守 `WORKFLOW.md` 中 GitHub 为调度真相、repo 为语义真相、Work Item 为执行入口的规则。
  - 遵守 `FR-0007` 已冻结的版本 gate 基线；`FR-0019` 只能叠加 `v0.6.0` operability gate。

## 测试与验证策略

- 单元测试：
  - `#233` 不新增单元测试；后续 `#234` 需要为矩阵 case builder、gate result 判定、same-path proof 与 fail-closed 分支补充单元测试。
- 集成/契约测试：
  - 后续 `#234` 必须覆盖 HTTP submit / status / result 与 CLI run / query 对同一 Core / task-record / store / envelope 语义的契约验证。
  - 后续 `#234` 必须覆盖 timeout、retry、concurrency、failure、log、metrics 的本地可复验回归矩阵。
- 手动验证：
  - `#233` 运行 formal spec / docs / workflow guards。
  - `#234` 在实现 PR 中记录 gate matrix 实际命令、输出位置、case evidence 与失败复验方式。

## TDD 范围

- 先写测试的模块：
  - `#234` 的 gate matrix case schema 与必填字段校验。
  - `#234` 的 gate result fail-closed 判定。
  - `#234` 的 HTTP / CLI same-path proof。
  - `#234` 的 timeout / retry / concurrency 回归 case。
  - `#234` 的 failure / log / metrics evidence 聚合。
- 暂不纳入 TDD 的模块与理由：
  - `#233` 仅为 formal spec，不写实现测试。
  - 外部 SaaS 监控、生产验收、分布式压测不属于 `v0.6.0` 本 FR 范围。
  - release closeout、tag、GitHub Release 由后续 parent closeout / release 流程处理，不由本 spec PR 验证。

## 并行 / 串行关系

- 可并行项：
  - `#223`、`#226`、`#229` 可在各自 worktree 中并行推进；`#233` 不修改其 ownership 文件。
  - `#233` 的 spec review 准备可与相邻事项的实现或审查并行。
- 串行依赖项：
  - `#234` 必须等待 `#233` 的 spec review 通过后进入实现。
  - `#235` 必须等待 `#233` 与 `#234` 的文档、实现、审查、门禁与 GitHub 状态一致后收口。
- 阻塞项：
  - 若 spec review 判定 `FR-0019` 边界不清或与 `FR-0007` 冲突，`#234` 不得开始实现。
  - 若无法证明 HTTP / CLI same-path 的共享 truth，`#235` 不得把 `v0.6.0` operability gate 作为完成证据。

## 进入实现前条件

- [ ] `spec review` 已通过。
- [ ] `FR-0019` 与 `FR-0007` 的承接关系已被 reviewer 接受。
- [ ] `FR-0016` 默认 policy 与 retry/concurrency 控制面语义已在 matrix case 中字段级固化。
- [ ] `FR-0017` 的结构化日志/指标/refs 语义已在 `failure_log_metrics` 维度字段级固化。
- [ ] `FR-0018` 的 HTTP/CLI 同 Core path 语义已在 `http_submit_status_result` 与 `cli_api_same_path` 维度字段级固化。
- [ ] timeout / retry / concurrency、failure / log / metrics、HTTP submit / status / result、CLI / API same-path 四类矩阵维度均无阻断性需求缺口。
- [ ] `contracts/README.md`、`data-model.md`、`risks.md` 已与 `spec.md` 对齐。
- [ ] `#234` 已确认作为 release gate matrix implementation 的后续执行入口。
