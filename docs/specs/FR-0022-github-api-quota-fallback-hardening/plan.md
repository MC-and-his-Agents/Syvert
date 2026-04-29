# FR-0022 GitHub API quota and fallback hardening implementation plan

## 关联信息

- item_key：`FR-0022-github-api-quota-fallback-hardening`
- Issue：`#274`
- item_type：`FR`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 exec-plan：`docs/exec-plans/CHORE-0275-fr-0022-github-api-quota-fallback-hardening.md`

## 实施目标

- 本次实施要交付的能力：
  - 冻结治理脚本 GitHub API quota 与 fallback contract。
  - 为 `#276` implementation Work Item 提供 decision-complete 的实现边界、测试边界与回滚边界。
  - 保持 `#275` 只做 formal spec，不混入实现代码。

## 分阶段拆分

- 阶段 1：formal spec closeout（`#275`）
  - 新增本 formal spec 套件。
  - 完成 spec review。
  - 合入主干后允许 `#276` 开始实现。
- 阶段 2：implementation（`#276`）
  - 实现当前进程 cached/non-merge lookup 与 uncached/live gate lookup 分离。
  - 收敛 `open_pr`、`governance_status`、`pr_guardian`、`spec_issue_sync`、`sync_repo_settings`、`review_poller` 的批准范围。
  - 补齐 governance 单元测试。
- 阶段 3：parent closeout（`#277`）
  - 核对 `#275` 与 `#276` 均已合入主干。
  - 收口 `#274` FR 与 `#273` Phase 的 GitHub 状态、仓内证据与主干事实。

## 实现约束

- 不允许触碰的边界：
  - `#275` PR 不得修改 `scripts/**`、`tests/**` 或业务 runtime。
  - `#276` 不得新增持久 cache、TTL、webhook 或外部调度服务。
  - `#276` 不得降低 merge gate 的 live integration recheck。
- 与上位文档的一致性约束：
  - `WORKFLOW.md` 仍定义 GitHub 为调度真相源。
  - `scripts/policy/integration_contract.json` 与 `scripts/integration_contract.py` 仍是 canonical integration contract 来源。
  - Phase `#273` 不作为 execution entrypoint；所有执行必须从 Work Item 进入。

## 测试与验证策略

- 单元测试：
  - `tests.governance.test_integration_contract` 覆盖 cache key、copy 返回、GraphQL 失败 hard fail。
  - `tests.governance.test_open_pr` 覆盖 canonicalization 使用 cached helper 与不可验证时保留 raw ref。
  - `tests.governance.test_governance_status` 覆盖 unverified 状态面。
  - `tests.governance.test_pr_guardian` 覆盖 merge gate live recheck 继续 hard fail 与 PR/checks 快照复用。
  - `tests.governance.test_spec_issue_sync` 覆盖 search fallback 使用策略。
  - `tests.governance.test_governance_gate` 覆盖 spec / governance PR 边界。
- 集成/契约测试：
  - 使用 mock 的 `gh api graphql` 与 `gh api repos/...`，不依赖真实 GitHub quota。
  - 使用现有 governance gate 验证 spec / implementation 分离。
- 手动验证：
  - 检查 `#274` 子 Work Item、`#275`、`#276`、`#277` 的 GitHub 状态与正文关系一致。

## TDD 范围

- 先写测试的模块：
  - `tests.governance.test_integration_contract`
  - `tests.governance.test_open_pr`
  - `tests.governance.test_governance_status`
  - `tests.governance.test_pr_guardian`
  - `tests.governance.test_spec_issue_sync`
- 暂不纳入 TDD 的模块与理由：
  - 真实 GitHub rate limit 行为不做 live integration test；该行为依赖外部 quota 状态，使用 mock contract 覆盖。
  - webhook 替代 polling 不属于本 FR scope。

## 并行 / 串行关系

- 可并行项：
  - `#276` 内部可并行实现 integration live state cache、sync_repo_settings hard fail、spec_issue_sync search fallback。
- 串行依赖项：
  - `#276` 必须等待 `#275` spec review 与合入。
  - `#277` 必须等待 `#275` 与 `#276` 合入主干。
- 阻塞项：
  - 若 spec review 要求新增持久 cache 或 webhook，必须先更新 `#274` / `#273` scope，不得在实现中擅自扩张。

## 进入实现前条件

- [ ] `spec review` 已通过
- [ ] 关键风险已记录并有缓解策略
- [ ] 关键依赖可用
