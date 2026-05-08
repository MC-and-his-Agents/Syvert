# GOV-0373 v1.1 Operation Taxonomy Release Closeout

## 关联信息

- Issue：`#373`
- item_key：`GOV-0373-v1-1-operation-taxonomy-release-closeout`
- item_type：`GOV`
- release：`v1.1.0`
- sprint：`2026-S23`
- Parent Phase：`#367`
- 关联 spec：docs/specs/FR-0368-operation-taxonomy-contract
- 关联 decision：docs/decisions/ADR-GOV-0373-v1-1-operation-taxonomy-release-closeout.md
- active 收口事项：`GOV-0373-v1-1-operation-taxonomy-release-closeout`
- 状态：`active`

## 目标

- 完成 `v1.1.0` Operation Taxonomy Foundation release closeout。
- 阶段 A carrier 合入后创建 `v1.1.0` annotated tag 与 GitHub Release。
- 阶段 B 回写 published truth，并关闭 Phase `#367`、FR `#368` 与 Work Item `#373`。

## 范围

- 本次纳入 release/sprint index、closeout evidence、ADR 与当前 exec-plan。
- 本次不纳入 runtime capability promotion、provider selector/fallback/marketplace、平台私有业务对象、上层 workflow 或 Python package publish。

## 当前停点

- `#369/#370/#371/#372` 均已 closed completed。
- 阶段 A carrier base：`27712c7b416c8ff8927e79851fd3ced4ed96e845`。
- 阶段 A PR `#378` 已合入，merge commit `52ae3b3757a7f88410d50e21670e5b158bbd7fd7`。
- `v1.1.0` annotated tag 已创建并推送，tag object `2f52b8979ef5195d058be1c1904b7fc55599825a`，target commit `52ae3b3757a7f88410d50e21670e5b158bbd7fd7`。
- GitHub Release `v1.1.0` 已创建：`https://github.com/MC-and-his-Agents/Syvert/releases/tag/v1.1.0`。
- 阶段 B 正在回写 published truth carrier。

## 验证摘要

- `python3 -m unittest tests.runtime.test_operation_taxonomy tests.runtime.test_operation_taxonomy_consumers tests.runtime.test_operation_taxonomy_admission_evidence`
  - 结果：通过，`Ran 16 tests`。
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`
  - 结果：通过，`Ran 79 tests`。
- `python3 -m unittest tests.runtime.test_platform_leakage tests.runtime.test_version_gate`
  - 结果：通过，`Ran 210 tests`。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/governance_gate.py --mode ci --base-sha <base> --head-sha <head> --head-ref issue-373-v1-1-0-operation-taxonomy-release-closeout`
  - 结果：通过。

## 最近一次 checkpoint 对应的 head SHA

- 阶段 A base：`27712c7b416c8ff8927e79851fd3ced4ed96e845`
- 阶段 A release carrier：`52ae3b3757a7f88410d50e21670e5b158bbd7fd7`
- 阶段 B PR live head 由 PR `headRefOid` 与 guardian merge gate 绑定。

## closeout 证据

- 可复验 evidence artifact：`docs/exec-plans/artifacts/GOV-0373-v1-1-operation-taxonomy-release-closeout-evidence.md`
- Release index：`docs/releases/v1.1.0.md`
- Sprint index：`docs/sprints/2026-S23.md`

## 风险

- 若阶段 A 前创建 tag / release，会违反两阶段 closeout。
- 若 proposed candidates 被写成 stable，会扩大 v1.1.0 scope。
- 若 tag target 不包含 release carrier，会破坏 published truth 可复验性。

## 回滚方式

- 阶段 A 前：revert carrier PR 即可。
- 阶段 A 后：若 tag/release 已创建但 truth 错误，先修正 main truth，再通过治理事项决定是否删除或重建发布锚点。
