# CHORE-0153-fr-0018-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0153-fr-0018-formal-spec-closeout`
- Issue：`#229`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0018-http-task-api-same-core-path/`
- 关联 PR：`待创建`
- 状态：`active`
- active 收口事项：`CHORE-0153-fr-0018-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0018` formal spec 套件，冻结最小 HTTP task API service surface 与 CLI/Core same-path contract，使后续实现只能通过共享 `TaskRecord` durable truth 暴露服务面。

## 范围

- 本次纳入：
  - `docs/specs/FR-0018-http-task-api-same-core-path/`
  - `docs/exec-plans/FR-0018-http-task-api-same-core-path.md`
  - `docs/exec-plans/CHORE-0153-fr-0018-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `docs/releases/**`
  - `docs/sprints/**`
  - 认证、多租户、RBAC、分布式队列、复杂查询 DSL、完整控制台
  - `#230/#231/#232` 的实现、证据与 parent closeout 正文

## 当前停点

- `issue-229-fr-0018-formal-spec` 已作为 `#229` 的独立 spec worktree 建立。
- 当前回合只允许修改 `FR-0018` formal spec 套件与两个 exec-plan，禁止越界到 runtime / tests / 相邻 FR。
- 本轮目标是把 HTTP `submit/status/result` service surface、same-core-path 边界、`TaskRecord` durable truth 复用约束、风险与后续拆分一次性落盘到 implementation-ready formal spec。
- 当前 formal spec 语义基线以 `49b1e4a3fa1dc61b8ffb866c50293bd8843d2fb4` 为恢复起点；在形成新的显式 checkpoint 前，后续 metadata-only 同步不改写该基线口径。

## 下一步动作

- 继续核对 `FR-0008`、`FR-0009` 与 `v0.6.0` 路线图边界，避免把 HTTP service 写成第二套执行面。
- 完成 formal spec suite、requirement container 与 active closeout exec-plan 的一致性校验。
- 运行 `spec_guard`、`docs_guard`、`workflow_guard`，把验证结果回写到本 exec-plan。
- 等待 `spec review`，通过后切换到 `#230` HTTP endpoint implementation，再由 `#231`、`#232` 继续收口。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 把“闭环后暴露第一个外部服务面”收敛为 implementation-ready 的最小 HTTP task API formal contract，并确保 API 与 CLI 继续共享同一条 Core / `TaskRecord` 路径。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0018` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 HTTP API 仍允许 adapter 直连、直接写任务记录或自建 envelope，下游 `#230/#231` 将失去同路径判定基线。
  - 若 `status/result` 不明确绑定 durable `TaskRecord` truth，CLI/API 回归证据无法形成单一真相链。

## 已验证项

- `sed -n '1,220p' /Users/mc/dev/syvert/AGENTS.md`
  - 结果：已核对仓库宪法、formal spec 与实现分离、GitHub/仓库双层真相与 Work Item 执行入口约束。
- `sed -n '1,260p' /Users/mc/dev/syvert/WORKFLOW.md`
  - 结果：已核对 Work Item / formal spec / exec-plan / merge gate 的 workflow contract。
- `sed -n '1,260p' /Users/mc/dev/syvert/spec_review.md`
  - 结果：已核对 formal spec 最小套件、review rubric 与进入实现前条件。
- `sed -n '1,260p' /Users/mc/dev/syvert/docs/specs/README.md`
  - 结果：已核对 formal spec 命名、聚合键与 optional artifacts 触发条件。
- `sed -n '1,260p' /Users/mc/dev/syvert/docs/specs/FR-0008-task-record-persistence/spec.md`
  - 结果：已核对 durable `TaskRecord`、状态机、终态 envelope 与 fail-closed 回读边界。
- `sed -n '1,260p' /Users/mc/dev/syvert/docs/specs/FR-0009-cli-task-query-and-core-path/spec.md`
  - 结果：已核对 CLI `run/query` same-path contract 与 query 回读语义。
- `sed -n '222,290p' docs/roadmap-v0-to-v1.md`
  - 结果：已核对 `v0.6.0` 目标、必备能力与明确不在范围内列表。
- `rg -n "v0\\.6|FR-0018|HTTP task API|same core path|submit|status|result|service surface|HTTP API" vision.md docs/roadmap-v0-to-v1.md docs`
  - 结果：已确认仓内尚无现成 `FR-0018` formal spec；直接相关权威边界来自 `v0.6.0` 路线图、`FR-0008` 与 `FR-0009`。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过

## 未决风险

- 若 `submit` 请求语义没有明确绑定到既有 shared request 投影，后续实现可能把 HTTP public capability 与 adapter-facing capability 混写。
- 若 `result` 对非终态缺少明确 `result_not_ready` contract，后续实现容易回退成 transport 私有空结果或伪造终态。
- 若 requirement container 与 closeout exec-plan 没有明确 `#230/#231/#232` 的串行关系，后续回合可能重复在实现中做 requirement 决策。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `docs/specs/FR-0018-http-task-api-same-core-path/`、`docs/exec-plans/FR-0018-http-task-api-same-core-path.md` 与当前 closeout exec-plan 的文档增量，不回退其他 FR 或实现改动。

## 最近一次 checkpoint 对应的 head SHA

- `49b1e4a3fa1dc61b8ffb866c50293bd8843d2fb4`
- review-sync 说明：在生成新的显式 checkpoint 之前，当前回合若只追加 PR / checks / guard / review metadata，同样按 metadata-only follow-up 处理，不伪装成新的语义 checkpoint。
