# GOV-0396 v1.2 Resource Governance Release Closeout

## 关联信息

- Issue：`#396`
- item_key：`GOV-0396-v1-2-resource-governance-release-closeout`
- item_type：`GOV`
- release：`v1.2.0`
- sprint：`2026-S24`
- Parent Phase：`#380`
- Parent FR：`#387`
- 关联 spec：docs/specs/FR-0387-resource-governance-admission-and-health-contract
- 关联 decision：docs/decisions/ADR-GOV-0396-v1-2-resource-governance-release-closeout.md
- active 收口事项：`GOV-0396-v1-2-resource-governance-release-closeout`
- 状态：`active`

## 目标

- 完成 `v1.2.0` Resource Governance Foundation release closeout。
- 阶段 A carrier 合入后创建 `v1.2.0` annotated tag 与 GitHub Release。
- 阶段 B 回写 published truth，并关闭 Phase `#380`、FR `#387` 与 Work Item `#396`。

## 范围

- 本次纳入 release/sprint index、closeout evidence、ADR 与当前 exec-plan。
- 本次不纳入 runtime carrier 修改、consumer migration、evidence rewrite、自动登录、自动刷新、修复循环、provider health SLA、新资源类型或 Python package publish。

## 当前停点

- `#388/#390/#391/#392` 均已 closed completed。
- 阶段 A carrier base：`eaec42d70ed432b7334eab19ef5ec5f69544f855`。
- 阶段 A PR 待创建。
- `v1.2.0` annotated tag 与 GitHub Release 待阶段 A carrier 合入后创建。
- 阶段 B published truth carrier 待 tag / GitHub Release 创建后回写。

## 验证摘要

- `python3 -m unittest tests.runtime.test_resource_governance_evidence tests.runtime.test_resource_health`
  - 结果：通过，`Ran 37 tests`。
- `python3 -m unittest tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision`
  - 结果：通过，`Ran 99 tests`。
- `python3 -m unittest tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store tests.runtime.test_resource_trace_store tests.runtime.test_resource_bootstrap tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_platform_leakage`
  - 结果：通过，`Ran 247 tests`。
- `python3 -m unittest tests.runtime.test_resource_governance_evidence tests.runtime.test_resource_health tests.runtime.test_adapter_capability_requirement tests.runtime.test_provider_capability_offer tests.runtime.test_provider_no_leakage_guard tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store tests.runtime.test_resource_trace_store tests.runtime.test_resource_bootstrap tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_platform_leakage`
  - 结果：通过，`Ran 383 tests`。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/governance_gate.py --mode ci --base-sha <base> --head-sha <head> --head-ref issue-396-v1-2-0-resource-governance-release-closeout`
  - 结果：通过。

## 最近一次 checkpoint 对应的 head SHA

- 阶段 A base：`eaec42d70ed432b7334eab19ef5ec5f69544f855`
- 阶段 A PR live head 由 PR `headRefOid` 与 merge gate 绑定。
- 阶段 B published truth follow-up 将记录 tag object、tag target 与 release URL。

## closeout 证据

- 可复验 evidence artifact：`docs/exec-plans/artifacts/GOV-0396-v1-2-resource-governance-release-closeout-evidence.md`
- Release index：`docs/releases/v1.2.0.md`
- Sprint index：`docs/sprints/2026-S24.md`

## 风险

- 若阶段 A 前创建 tag / release，会违反两阶段 closeout。
- 若把 resource governance foundation 写成自动登录 / 自动刷新 / 修复循环，会扩大 v1.2.0 scope。
- 若 health status 被写成 provider SLA，会破坏 Core / Provider 边界。
- 若 tag target 不包含 release carrier，会破坏 published truth 可复验性。

## 回滚方式

- 阶段 A 前：revert carrier PR 即可。
- 阶段 A 后：若 tag/release 已创建但 truth 错误，先修正 main truth，再通过治理事项决定是否删除或重建发布锚点。
