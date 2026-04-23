# CHORE-0147-fr-0016-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0147-fr-0016-formal-spec-closeout`
- Issue：`#223`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0016-minimal-execution-controls/`
- 关联 PR：`#237`
- 状态：`active`
- active 收口事项：`CHORE-0147-fr-0016-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0016` formal spec 套件，冻结 `ExecutionControlPolicy`、attempt timeout、基础 retry 与 fail-fast concurrency gate 的最小运行时 contract。

## 范围

- 本次纳入：
  - `docs/specs/FR-0016-minimal-execution-controls/`
  - `docs/exec-plans/FR-0016-minimal-execution-controls.md`
  - `docs/exec-plans/CHORE-0147-fr-0016-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `.github/**`
  - HTTP API、runtime timeout / retry / concurrency 实现、release gate runtime、release / sprint 索引与 GitHub closeout

## 当前停点

- `issue-223-fr-0016-formal-spec` 已作为 `#223` 的独立 spec worktree 建立。
- 当前回合只允许修改 `FR-0016` formal spec 套件与两个 exec-plan，禁止越界到 runtime、tests、HTTP API 或相邻 FR。
- formal spec 套件已落盘并创建当前受审 spec PR `#237`；当前停点是等待 GitHub checks、spec review、guardian 与受控 merge gate。

## 下一步动作

- 在 PR `#237` 上消费 GitHub checks、spec review、guardian 与 merge gate 反馈。
- 若后续只追加 PR / checks / checkpoint metadata，则保持 review-sync follow-up 口径，不伪装成新的 requirement 语义变更。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 把最小执行控制从调用方/adapter 私有细节收敛为 Core-owned formal contract，使后续 runtime、observability、HTTP API 与 gate matrix 都能消费同一控制语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0016` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 timeout / retry / concurrency contract 不冻结，`FR-0017` 无法稳定记录控制结果，`FR-0018` HTTP API 也无法证明没有绕过 Core。
  - 若当前 spec 把 retry 或 concurrency 扩张为 DSL / queue / scheduler，会越过 `v0.6.0` 最小边界并阻塞后续实现。

## 已验证项

- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`docs/specs/README.md` 的 formal spec 与 Work Item 边界。
- 已核对 `FR-0005` 错误模型、`FR-0008` TaskRecord、`FR-0009` CLI/Core 同路径、`FR-0010` 到 `FR-0015` 资源相关 contract。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-223-fr-0016-formal-spec`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 223 --item-key CHORE-0147-fr-0016-formal-spec-closeout --item-type CHORE --release v0.6.0 --sprint 2026-S19 --title 'docs(spec): 收口 FR-0016 最小执行控制 formal spec' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建当前受审 spec PR `#237 https://github.com/MC-and-his-Agents/Syvert/pull/237`
- `python3 scripts/pr_guardian.py review 237`
  - 结果：`REQUEST_CHANGES`；阻断点为 retryable outcome 字段漂移、attempt outcome 与 admission/聚合事实混用、缺少数据迁移说明
- 已修复：移除 caller-visible `retryable_outcomes` 字段语义，固定 Core retryable rule 为 `execution_timeout` 与 `error.category=platform`；新增 `ExecutionControlEvent` 区分 `concurrency_rejected` 与 `retry_exhausted`；补充数据模型与迁移说明
- `python3 scripts/pr_guardian.py review 237`
  - 结果：`REQUEST_CHANGES`；阻断点为 post-accepted retry 重新获取 concurrency slot 的状态转移未闭合、`on_limit` public contract 不一致、默认 policy 未冻结
- 已修复：冻结完整默认 `ExecutionControlPolicy`；将 `on_limit=reject` 定义为 caller-visible required field；补充 `retry_concurrency_rejected` control event 与同一 TaskRecord failed 终态语义

## 未决风险

- timeout 若落在 adapter 私有层，后续 CLI / HTTP / TaskRecord 无法共享同一运行时真相。
- retry 若默认覆盖 `invalid_input`、`unsupported` 或一般 `runtime_contract`，会掩盖 contract violation。
- concurrency 若引入 queue / priority / fairness，会提前进入调度器语义并扩大 HTTP API 范围。
- late completion 若能改写终态，会破坏 TaskRecord durable truth 与 guardian / gate 可复验性。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0016` formal spec 套件与当前 closeout exec-plan 的文档增量，不回退其他 FR、runtime 或治理工件。

## 最近一次 checkpoint 对应的 head SHA

- `952c26d6240df61eb714a6c9f388541dd5197d31`
