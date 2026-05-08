# CHORE-0392-v1-2-resource-governance-evidence 执行计划

## 关联信息

- item_key：`CHORE-0392-v1-2-resource-governance-evidence`
- Issue：`#392`
- item_type：`CHORE`
- release：`v1.2.0`
- sprint：`2026-S24`
- Parent Phase：`#380`
- Parent FR：`#387`
- 关联 spec：`docs/specs/FR-0387-resource-governance-admission-and-health-contract/`
- 上游依赖：`#390` runtime carrier 已由 PR `#393` 合入并关闭；`#391` consumer boundary 已由 PR `#394` 合入并关闭
- 关联 PR：待创建

## 目标

- 交付可复验 evidence artifact，证明 FR-0387 resource governance health contract 在 fake/reference runtime paths 中成立。
- 证据供后续 release closeout GOV Work Item 消费；本事项不创建 release closeout。

## 范围

- 本次纳入：
  - `docs/exec-plans/artifacts/CHORE-0392-v1-2-resource-governance-evidence.md`
  - `tests/runtime/test_resource_governance_evidence.py`
  - evidence 覆盖 healthy admission、expired healthy -> stale rejection、missing evidence -> unknown fail-closed、invalid_contract、pre-admission invalid 不改库存、active lease invalid Core-owned invalidation、public projection redaction。
- 本次不纳入：
  - runtime carrier 修改。
  - consumer boundary 修改。
  - 自动登录、刷新、修复循环。
  - release closeout、GitHub Release 或 tag。

## 当前停点

- 已实现 evidence artifact 与 replay tests。
- 待完整回归、commit、PR、review、merge closeout。

## 下一步动作

- 跑 #392 范围 evidence / runtime / consumer 回归与 governance gate。
- 创建 PR，完成 review/merge 后关闭 #392。

## 当前 checkpoint 推进的 release 目标

- `v1.2.0 Resource Governance Foundation` evidence。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：承接 #390/#391 后，为 release closeout 提供可消费证据。
- 阻塞：最终 GOV release/Phase/FR closeout 必须等本事项合入后创建。

## 已验证项

- `python3 -m py_compile tests/runtime/test_resource_governance_evidence.py`：通过。
- `python3 -m unittest tests.runtime.test_resource_governance_evidence tests.runtime.test_resource_health`：37 tests passed。
- `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard`：99 tests passed。
- `python3 -m unittest tests.runtime.test_resource_governance_evidence tests.runtime.test_resource_health tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store tests.runtime.test_resource_trace_store tests.runtime.test_resource_bootstrap tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_platform_leakage`：383 tests passed。
- `python3 scripts/spec_guard.py --mode ci --all`：通过。
- `python3 scripts/docs_guard.py --mode ci`：通过。
- `python3 scripts/workflow_guard.py --mode ci`：通过。

## Review 处理记录

- 暂无。

## 未决风险

- evidence artifact 与 runtime truth 漂移。当前由 `test_resource_governance_evidence` 从 runtime 重新构建 report 并与 artifact JSON 快照逐字段比较。
- evidence 越界表达自动恢复机制。当前 artifact non-goals 明确 `automatic_login=false`、`automatic_refresh=false`、`repair_loop=false`。
- release closeout 被提前创建。当前 PR 只包含 #392 artifact/tests/exec-plan。

## 回滚方式

- 使用独立 revert PR 回滚 evidence artifact、tests 与本 exec-plan；#390/#391 可保留。

## 最近一次 checkpoint 对应的 head SHA

- `ad2d49aa8fb9853260e579650c20856973e7b007`
- Current HEAD may include a metadata-only checkpoint follow-up that records this verified implementation checkpoint.
