# CHORE-0331-fr-0023-third-party-resource-proof-bridge 执行计划

## 关联信息

- item_key：`CHORE-0331-fr-0023-third-party-resource-proof-bridge`
- Issue：`#331`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0023-third-party-adapter-entry-path/`
- 关联 decision：
- 关联 PR：
- active 收口事项：`CHORE-0331-fr-0023-third-party-resource-proof-bridge`
- 状态：`active`

## 目标

- 修复 `FR-0023` 第三方 Adapter identity 边界与 `FR-0027` resource profile proof coverage 之间的 formal truth 缺口，使 `#310` 可以使用真实第三方 `adapter_key`，同时不得绕过 `FR-0027` 的 approved profile proof、tuple、execution path 与 fail-closed 规则。

## 范围

- 本次纳入：
  - `docs/specs/FR-0023-third-party-adapter-entry-path/spec.md`
  - `docs/specs/FR-0023-third-party-adapter-entry-path/plan.md`
  - `docs/specs/FR-0023-third-party-adapter-entry-path/data-model.md`
  - `docs/specs/FR-0023-third-party-adapter-entry-path/contracts/README.md`
  - `docs/specs/FR-0023-third-party-adapter-entry-path/risks.md`
  - `docs/exec-plans/CHORE-0331-fr-0023-third-party-resource-proof-bridge.md`
- 本次不纳入：
  - `#310` implementation files
  - `tests/runtime/contract_harness/**`
  - contract harness implementation
  - `syvert/resource_capability_evidence.py`
  - `tests/**`
  - Provider offer、compatibility decision、selector、priority、fallback 或 marketplace

## 当前停点

- `#310` / PR `#330` guardian 已多次暴露同类阻断：真实第三方 `adapter_key` 不能伪装成 `xhs` / `douyin`，但裸引用 `FR-0027` 当前双参考 proof 又无法满足 `reference_adapters` 覆盖。
- `FR-0027` 当前 proof truth 自洽：approved shared profile proof 只覆盖 `xhs`、`douyin`，裸借用该 proof 的第三方 declaration 必须 fail-closed。
- 本事项采用 formal/evidence bridge 策略：`FR-0023` 定义第三方 contract entry 的 adapter-specific proof admission carrier；该 carrier 必须绑定真实第三方 `adapter_key`、`FR-0027` approved shared profile proof、同一 execution slice 与 fixture / manifest 证据，不能修改或放宽 `FR-0027` 双参考 proof 本身。
- PR `#334` 首轮 guardian 结论为 `REQUEST_CHANGES`：指出 admission 被放在完整 `FR-0027` adapter coverage 校验之后，导致真实第三方 `adapter_key` 会先失败、bridge 不可达。已修正为 admission 参与 proof binding 的 adapter coverage 子条件；`FR-0027` shape、single proof ref、approved shared proof lookup、tuple 与 execution path 仍原样校验。

## 下一步动作

- 更新 `FR-0023` formal suite，冻结 `ThirdPartyResourceProofAdmission` 语义。
- 推送并开 spec PR。
- 运行 guardian review；若 guardian 继续指出系统性冲突，先复盘 bridge 语义再修正。
- checks 与 guardian 通过后受控合并，并回写 `#310` / PR `#330` unblock comment。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 第三方 Adapter contract test entry 提供可实现、可审查的 resource proof admission formal input，使开放接入路径不再在真实第三方 `adapter_key` 与 `FR-0027` proof coverage 之间形成二选一。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0023` contract test entry 的 formal/evidence bridge Work Item。
- 阻塞：
  - `#310` / PR `#330` 必须等待本 bridge 合入后，才能在真实第三方 `adapter_key` 下实现 resource proof admission，而不是伪装为 reference adapter 或跳过 proof coverage。

## 已验证项

- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class 为 `spec`，变更类别为 `docs, spec`。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-331-fr-0023-adapter-resource-proof-admission`
  - 初次提交前结果：通过。
  - 提交 `abd22de2455de000d5295298003b7915bb8bc0fc` 后结果：失败，提示 active exec-plan 缺少可解析的 40 位 checkpoint head SHA。
  - 补齐 checkpoint SHA 后结果：通过。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 334 --post-review --json-output /tmp/syvert-pr-334-guardian.json`
  - 首轮结果：`REQUEST_CHANGES`，`safe_to_merge=false`；阻断为 admission step 在完整 `FR-0027` adapter coverage 校验之后不可达。
  - 修正：已将 `ThirdPartyResourceProofAdmission` 调整为 proof binding 判定中的 adapter coverage 子条件。
- 首轮 guardian 修正后复跑：
  - `python3 scripts/spec_guard.py --mode ci --all`：通过。
  - `python3 scripts/docs_guard.py --mode ci`：通过。
  - `python3 scripts/workflow_guard.py --mode ci`：通过。
  - `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`：通过，PR class 为 `spec`，变更类别为 `docs, spec`。
  - `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-331-fr-0023-adapter-resource-proof-admission`：通过。

## 未决风险

- 本事项只冻结 formal/evidence bridge，不实现 `#310` contract harness。
- 若后续发现需要把 third-party admission entry 升格为 `syvert/resource_capability_evidence.py` 中的 runtime evidence index，应另由 implementation Work Item 证明必要性；本 spec PR 不混入实现代码。
- 任何未带 adapter-specific admission proof 的第三方 `adapter_key` 继续 fail-closed；本 bridge 不批准裸借用 `xhs` / `douyin` reference proof。

## 回滚方式

- 使用独立 revert PR 撤销本事项对 `FR-0023` formal suite 与本 exec-plan 的增量修改。
- 若 bridge 语义需要改写 `FR-0027` proof carrier 本身，必须另建 `FR-0027` formal/evidence Work Item，不在 `#310` 实现 PR 中隐式绕过。

## 最近一次 checkpoint 对应的 head SHA

- `abd22de2455de000d5295298003b7915bb8bc0fc`
- `05759c988297ce688cda50b98609dfa71b285564`
- 说明：该 checkpoint 首次把第三方真实 `adapter_key` 的 adapter-specific resource proof admission bridge、`FR-0023` formal suite 与 active exec-plan 同步落盘；后续若只补 PR / guardian / merge gate 元数据，则作为 review-sync follow-up，不把版本化 exec-plan 退化为 live head 状态面。
