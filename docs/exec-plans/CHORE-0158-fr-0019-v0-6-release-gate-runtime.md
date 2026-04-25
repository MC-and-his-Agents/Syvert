# CHORE-0158 FR-0019 v0.6 release gate runtime 执行计划

## 关联信息

- item_key：`CHORE-0158-fr-0019-v0-6-release-gate-runtime`
- Issue：`#234`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 父 FR：`#222`
- 关联 spec：`docs/specs/FR-0019-v0-6-operability-release-gate/`
- 状态：`active`

## 目标

- 在 `FR-0019` 已冻结边界内实现 `v0.6.0` operability release gate runtime。
- 产出 machine-readable `OperabilityGateResult`，覆盖 mandatory matrix：`timeout_retry_concurrency`、`failure_log_metrics`、`http_submit_status_result`、`cli_api_same_path`。
- gate runner 只消费已合入的 runtime/evidence truth，不替代 guardian、merge gate、`FR-0007` baseline gate 或 release closeout。

## 范围

- 本次纳入：
  - `syvert/operability_gate.py`
  - `tests/runtime/test_operability_gate.py`
  - `docs/exec-plans/CHORE-0158-fr-0019-v0-6-release-gate-runtime.md`
- 本次不纳入：
  - 修改 `FR-0019` formal spec 语义
  - tag / GitHub Release / phase closeout
  - 外部 SaaS dashboard、生产压测、分布式队列或线上 SLO/SLA
  - 重写 `FR-0007` version gate、guardian 或 `merge_pr`

## 当前停点

- `#224/#225` 已完成 `FR-0016` runtime 与 parent closeout，主干证据可供 `timeout_retry_concurrency` 维度消费。
- `#227/#228` 已完成 `FR-0017` runtime 与 parent closeout，主干证据可供 `failure_log_metrics` 维度消费。
- `#230/#231/#232` 已完成 `FR-0018` HTTP runtime、same-path regression evidence 与 parent closeout，主干证据可供 `http_submit_status_result` / `cli_api_same_path` 维度消费。
- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-234-fr-0019-v0-6-0`
- 当前主干基线：`7a1439052f85f26ae34e7770dd7de3b4c73f7fb3`

## 下一步动作

- 补齐 `syvert/operability_gate.py` 与 `tests/runtime/test_operability_gate.py`。
- 运行新增专项测试、runtime regression、全量 unittest discover 与 governance gate。
- 创建 implementation PR，等待 CI、reviewer、guardian。
- 合入后同步 GitHub issue / Project 状态、fast-forward main，并退役 worktree / branch。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 提供可机判、可本地复验、fail-closed 的 operability gate result，使 `#235` 能基于主干事实收口 `FR-0019` parent。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0019` release gate runtime implementation Work Item。
- 阻塞：
  - `#235` parent closeout 依赖本事项合入后的 gate result runtime 和测试证据。
  - `#236` phase / release closeout 依赖 `FR-0019` parent 完成。

## 已验证项

- `python3 scripts/create_worktree.py --issue 234 --class implementation`
  - 结果：通过，创建 `issue-234-fr-0019-v0-6-0` worktree / branch，base SHA 为 `7a1439052f85f26ae34e7770dd7de3b4c73f7fb3`。
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/234`
  - 结果：已确认 `#234` open，item_key / release / sprint / 父 FR 与本执行计划一致。
- `python3 -m py_compile syvert/operability_gate.py`
  - 结果：通过。
- `python3 -m unittest tests.runtime.test_operability_gate`
  - 结果：首轮通过，`Ran 10 tests`，`OK`；修复 guardian 一轮阻断后再次通过，`Ran 13 tests`，`OK`；修复 guardian 二轮阻断后再次通过，`Ran 17 tests`，`OK`。
- `python3 -m unittest tests.runtime.test_runtime tests.runtime.test_http_api tests.runtime.test_cli_http_same_path tests.runtime.test_task_record_store tests.runtime.test_version_gate tests.runtime.test_operability_gate`
  - 结果：首轮通过，`Ran 251 tests`，`OK`；修复 guardian 一轮阻断后再次通过，`Ran 254 tests`，`OK`；修复 guardian 二轮阻断后再次通过，`Ran 258 tests`，`OK`。
- `python3 -m unittest discover -s tests`
  - 结果：通过，`Ran 376 tests`，`OK`；修复 guardian 一轮阻断后再次通过，`Ran 376 tests`，`OK`；修复 guardian 二轮阻断后再次通过，`Ran 376 tests`，`OK`。
- `python3 scripts/governance_gate.py --mode local --base-ref origin/main`
  - 结果：通过，`governance-gate 通过。`；修复 guardian 一轮、二轮阻断后均再次通过。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-33f9463.json`
  - 结果：`REQUEST_CHANGES`；指出 `execution_revision` 未与 evidence 绑定、case-level `evidence_refs` 缺失未 fail-closed、额外未批准 dimension 未拒绝。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-51b1ff4.json`
  - 结果：`REQUEST_CHANGES`；指出 mandatory matrix assertions 未对 actual gate input 求值、`baseline_gate_ref` 只校验非空、`gate_id` / `matrix_version` 未冻结。

## 待完成

- PR / CI / reviewer / guardian / merge gate。
- 合入后关闭 `#234` 并同步 Project。

## 未决风险

- 若 gate result 缺失 `baseline_gate_ref`、mandatory case、metrics snapshot 或 evidence ref，必须 fail-closed，不能为了 release closeout 默认放行。
- 若把 `FR-0019` runtime 扩展成生产观测平台，会超出 `v0.6.0` 本地可复验 gate 范围。

## 回滚方式

- 使用独立 revert PR 撤销 `syvert/operability_gate.py`、`tests/runtime/test_operability_gate.py` 与本 exec-plan 增量。
- 不回滚 `FR-0016`、`FR-0017`、`FR-0018` 已合入 runtime / evidence。

## 最近一次 checkpoint 对应的 head SHA

- 当前主干基线：`7a1439052f85f26ae34e7770dd7de3b4c73f7fb3`。
- 当前可恢复 checkpoint：`f2cad8f6d53341bdaf8b9c31948950b6ad908c0a`，包含 gate runner、mandatory matrix validator、revision/evidence 绑定校验、case-level evidence fail-closed、allowed dimension 校验、baseline ref 校验、gate/matrix identity freeze、actual_result 断言求值、专项测试与验证证据；后续若只更新 review / merge gate / closeout metadata，不推进新的 runtime 语义 checkpoint。
