# CHORE-0276 FR-0022 GitHub API quota runtime hardening

## 关联信息

- item_key：`CHORE-0276-fr-0022-github-api-quota-runtime`
- Issue：`#276`
- item_type：`CHORE`
- release：`v0.7.0`
- sprint：`2026-S20`
- 关联 spec：`docs/specs/FR-0022-github-api-quota-fallback-hardening/`
- 关联 decision：
- 关联 PR：

## 目标

- 本次执行要交付的能力：
  - 为 governance 脚本减少重复 GitHub REST / GraphQL 读取。
  - 在非合并状态面允许缓存与 unverified 状态表达。
  - 保持 merge gate 的最终 live recheck hard-fail，不把 stale 状态当作通过。

## 范围

- 本次纳入：
  - `integration_contract` 的进程内 integration live state cache 与 uncached helper。
  - `pr_guardian merge-if-safe` 的 live recheck uncached 读取与 checks 复核收敛。
  - `spec_issue_sync` 的 mirror issue 批量索引，减少逐 spec `search/issues`。
  - `sync_repo_settings` rulesets 读取失败 hard fail。
  - `review_poller` unchanged PR 不触发 guardian，也不无意义写回 state。
  - 相关 governance 单测。
- 本次不纳入：
  - 不新增持久 cache、TTL cache、webhook 或跨进程 cache。
  - 不降低 merge gate live recheck 的最终阻断语义。
  - 不关闭 `#274` / `#273`；关闭动作由 `#277` 收口。

## 当前停点

- `#275` formal spec 已合入主干。
- 当前工作树正在实现 `#276` runtime hardening。

## 下一步动作

- 运行目标单测与 governance/docs gates。
- 提交并打开 implementation PR。
- guardian 审查通过后 squash merge。
- 合入后进入 `#277` closeout，核对 GitHub 状态与主干事实。

## 当前 checkpoint 推进的 release 目标

- 推进 `v0.7.0` 下 `FR-0022` GitHub API quota 与 fallback hardening 的实现阶段。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0022` implementation Work Item。
- 阻塞：阻塞 `#277` parent closeout、`#274` FR closeout 与 `#273` Phase closeout。

## 已验证项

- 已通过：
  - `python3.11 -m unittest tests.governance.test_review_poller`
  - `python3.11 -m unittest tests.governance.test_sync_repo_settings`
  - `python3.11 -m unittest tests.governance.test_spec_issue_sync`
  - `python3.11 -m unittest tests.governance.test_integration_contract`
  - `python3.11 -m unittest tests.governance.test_pr_guardian`
  - `python3.11 -m unittest tests.governance.test_open_pr`
  - `python3.11 -m unittest tests.governance.test_governance_status`
  - `python3.11 -m unittest tests.governance.test_governance_gate`
  - `python3.11 -m unittest tests.governance.test_integration_contract tests.governance.test_open_pr tests.governance.test_governance_status tests.governance.test_pr_guardian tests.governance.test_spec_issue_sync tests.governance.test_governance_gate tests.governance.test_review_poller tests.governance.test_sync_repo_settings`
  - `python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - `python3.11 scripts/docs_guard.py --mode ci`

## 未决风险

- guardian 审查可能要求进一步拆分 `pr_guardian` merge gate checks 顺序；若发生，以保持最终合并前复核为准。
- `spec_issue_sync` 仍只读取前 100 个 issue；若 mirror issue 超过该页未命中，保留单 spec `search/issues` fallback。

## 回滚方式

- 使用独立 revert PR 撤销本 PR 对 `scripts/**`、`tests/**` 与本 exec-plan 的修改。
- 若 GitHub 事项状态需要回滚，使用 REST PATCH 恢复 `#276`、`#274`、`#273` 的状态与评论，不影响主干历史。

## 最近一次 checkpoint 对应的 head SHA

- `c37e2ed595041dfe758965e9abefb450749af699`
- 当前为 `#276` implementation checkpoint；最终 PR head 以合入前 guardian 复核记录为准。
