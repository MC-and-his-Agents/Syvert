# CHORE-0358 v0.9.0 external provider sample evidence 执行计划

## 关联信息

- item_key：`CHORE-0358-v0-9-external-provider-sample-evidence`
- Issue：`#358`
- item_type：`CHORE`
- release：`v0.9.0`
- sprint：`2026-S22`
- 上位 Phase：`#354`
- 上位 FR：`#355`
- 关联 spec：`docs/specs/FR-0355-v0-9-real-provider-compatibility-evidence/`
- 关联 decision：
- active 收口事项：`CHORE-0358-v0-9-external-provider-sample-evidence`
- 状态：`active`

## 目标

- 交付 `FR-0355` 要求的 external provider sample evidence。
- 证明 external provider sample 可以经过 compatibility decision 并进入 Adapter-bound execution evidence。
- 生成可被 `FR-0351` 的 `provider_compatibility_sample` gate item 消费的仓内 evidence。

## 范围

- 本次纳入：
  - `syvert/real_provider_sample_evidence.py`
  - `tests/runtime/test_real_provider_sample_evidence.py`
  - `docs/exec-plans/artifacts/CHORE-0358-v0-9-external-provider-sample-evidence.md`
  - `docs/exec-plans/CHORE-0358-v0-9-external-provider-sample-evidence.md`
- 本次不纳入：
  - provider selector、fallback、marketplace 或 Core provider registry
  - provider 产品正式支持声明
  - 新 public operation 或 approved slice 扩展
  - `v0.9.0` release tag / GitHub Release publish closeout

## 当前停点

- GitHub Work Item `#358` 已创建。
- 标准 worktree `issue-358-v0-9-0-external-provider-sample-evidence` 已创建。
- external provider sample evidence helper、tests、artifact 与 exec-plan 正在落地。

## 下一步动作

- 执行 targeted runtime tests。
- 执行 dual reference、third-party entry、API / CLI same Core path 与 no-leakage 回归。
- 执行 docs / governance / scope / whitespace gates。
- 提交、推送、创建 PR。
- GitHub checks 通过后运行 guardian。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.9.0` 提供真实 provider compatibility sample evidence。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.9.0` implementation / evidence 主体事项。
- 阻塞：`v0.9.0` release closeout 需要消费本事项合入后的 evidence artifact。

## 已验证项

- `python3 -m py_compile syvert/real_provider_sample_evidence.py tests/runtime/test_real_provider_sample_evidence.py`：通过
- `python3 -m unittest tests.runtime.test_real_provider_sample_evidence`：通过
- `python3 -m unittest tests.runtime.test_adapter_provider_compatibility_decision tests.runtime.test_provider_no_leakage_guard tests.runtime.test_real_provider_sample_evidence`：通过
- `python3 -m unittest tests.runtime.test_real_adapter_regression tests.runtime.test_third_party_adapter_contract_entry tests.runtime.test_cli_http_same_path`：通过
- `python3 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD`：通过
- `python3 scripts/docs_guard.py --mode ci`：通过
- `python3 scripts/workflow_guard.py --mode ci`：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`：通过
- `python3 scripts/pr_scope_guard.py --class implementation --base-ref origin/main --head-ref HEAD`：通过，变更类别为 `docs, implementation`
- `git diff --check origin/main..HEAD`：通过

## 未决风险

- 本事项不发布 `v0.9.0` tag 或 GitHub Release；release closeout 需要后续 Work Item。
- external provider sample 是可复验 fixture / replay sample，不是 live network provider support。
- 若 guardian 认为 evidence 仍不足以代表 external provider sample，需要在本事项内补充更具体的 fixture provenance，而不是降低 gate。

## 回滚方式

- 使用独立 revert PR 撤销本事项新增的 helper、tests、evidence artifact 与 exec-plan。

## 最近一次 checkpoint 对应的 head SHA

- `5d505179f3ea4d0508e913e407f39b4c73ba8874`
- 当前 PR head 由 guardian state / GitHub checks 绑定，不把本字段作为 merge gate 的 live head 替代来源。
