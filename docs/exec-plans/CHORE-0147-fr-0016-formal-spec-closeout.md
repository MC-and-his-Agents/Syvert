# CHORE-0147-fr-0016-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0147-fr-0016-formal-spec-closeout`
- Issue：`#223`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0016-minimal-execution-controls/`
- 关联 PR：`待创建`
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
- formal spec 初稿已落盘，当前停点是运行本地门禁、生成 checkpoint commit，并通过受控入口创建 spec PR。

## 下一步动作

- 运行 `spec_guard`、`docs_guard`、`workflow_guard` 与 `governance_gate`。
- 生成中文 Conventional Commit checkpoint。
- 使用 `scripts/open_pr.py --class spec` 创建 `#223` 的 formal spec PR。
- 后续在该 PR 上消费 spec review、guardian、CI 与受控 merge gate。

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
- 待运行：`python3 scripts/spec_guard.py --mode ci --all`
- 待运行：`python3 scripts/docs_guard.py --mode ci`
- 待运行：`python3 scripts/workflow_guard.py --mode ci`
- 待运行：`python3 scripts/governance_gate.py --mode ci --base-sha "$(git merge-base origin/main HEAD)" --head-sha "$(git rev-parse HEAD)" --head-ref issue-223-fr-0016-formal-spec`

## 未决风险

- timeout 若落在 adapter 私有层，后续 CLI / HTTP / TaskRecord 无法共享同一运行时真相。
- retry 若默认覆盖 `invalid_input`、`unsupported` 或一般 `runtime_contract`，会掩盖 contract violation。
- concurrency 若引入 queue / priority / fairness，会提前进入调度器语义并扩大 HTTP API 范围。
- late completion 若能改写终态，会破坏 TaskRecord durable truth 与 guardian / gate 可复验性。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0016` formal spec 套件与当前 closeout exec-plan 的文档增量，不回退其他 FR、runtime 或治理工件。

## 最近一次 checkpoint 对应的 head SHA

- `待生成`
