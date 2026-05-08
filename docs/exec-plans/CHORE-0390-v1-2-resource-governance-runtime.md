# CHORE-0390-v1-2-resource-governance-runtime 执行计划

## 关联信息

- item_key：`CHORE-0390-v1-2-resource-governance-runtime`
- Issue：`#390`
- item_type：`CHORE`
- release：`v1.2.0`
- sprint：`2026-S24`
- Parent Phase：`#380`
- Parent FR：`#387`
- 关联 spec：`docs/specs/FR-0387-resource-governance-admission-and-health-contract/`
- 关联 PR：待创建

## 目标

- 交付 FR-0387 的最小 runtime carrier：`CredentialMaterial`、`SessionHealth`、`ResourceHealthEvidence`、`ResourceAdmissionDecision` 与 `ResourceInvalidationReason`。
- 在不改变默认 resource lifecycle acquire/release 行为的前提下，提供显式 resource health admission 与 active lease invalidation helper。

## 范围

- 本次纳入：
  - account credential material 的私有边界与脱敏 public projection。
  - health evidence contract validation、freshness / expiry projection、unknown/stale/invalid/healthy admission decision。
  - malformed、unredacted、context-mismatched evidence 的 `invalid_contract` fail-closed。
  - active lease invalid evidence 通过既有 `release(target_status_after_release=INVALID)` 收口。
- 本次不纳入：
  - AdapterRequirement / ProviderOffer / compatibility decision migration。
  - fake/reference/real evidence artifact。
  - 自动登录、刷新、修复循环或后台再验证。
  - release closeout、GitHub Release 或 tag。

## 当前停点

- 已实现 runtime carrier 与测试。
- 待提交、PR、review、merge closeout。

## 下一步动作

- 新增 `syvert/resource_health.py`。
- 新增 `tests/runtime/test_resource_health.py`。
- 跑 #390 范围 runtime 回归与 governance gate。
- 创建 PR，完成 review/merge 后关闭 #390。

## 当前 checkpoint 推进的 release 目标

- `v1.2.0 Resource Governance Foundation` runtime carrier。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：承接 #388 formal spec 后的第一项 runtime 实现。
- 阻塞：#391 consumer boundary 与 #392 evidence 必须等本事项合入后执行。

## 已验证项

- `python3 -m unittest tests.runtime.test_resource_health tests.runtime.test_resource_lifecycle tests.runtime.test_resource_lifecycle_store tests.runtime.test_resource_trace_store tests.runtime.test_resource_bootstrap tests.runtime.test_real_adapter_regression tests.runtime.test_cli_http_same_path tests.runtime.test_provider_no_leakage_guard tests.runtime.test_runtime`：245 tests passed。
- `python3 -m py_compile syvert/resource_health.py tests/runtime/test_resource_health.py`：通过。
- `python3 scripts/spec_guard.py --mode ci --all`：通过。
- `python3 scripts/docs_guard.py --mode ci`：通过。
- `python3 scripts/workflow_guard.py --mode ci`：通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-390-v1-2-resource-governance-runtime-carrier`：通过。

## Review 处理记录

- PR guardian 第一轮 `REQUEST_CHANGES`：
  - P1：mapping evidence 会静默丢弃未知私有字段。处理：`resource_health_evidence_from_dict()` 对未知字段 fail-closed，并补 `cookies` extra payload 回归。
  - P1：active lease invalidation 未校验 `bundle_id`。处理：校验 evidence `bundle_id` 必须与 active lease 一致，不一致返回 `invalid_contract`，并补回归。
- PR guardian 第二轮 `REQUEST_CHANGES`：
  - P1：health-gated admission 未校验 account `CredentialMaterial`。处理：admission 对所有 account resource 执行 material contract 校验，缺失或 adapter 绑定不一致返回 `credential_material_contract_invalid`，并补回归。
  - P1：active lease invalidation 允许缺失 `bundle_id`。处理：active invalidation 要求 evidence 必须携带 `bundle_id`，缺失返回 `invalid_contract`，并补回归。
- PR guardian 第三轮 `REQUEST_CHANGES`：
  - P1：`CredentialMaterial` public projection 暴露私有字段名。处理：projection 只暴露 material boundary、redaction 状态、字段数量与字段已脱敏标记，不暴露 material keys，并补回归。
  - P1：active lease invalidation 未绑定当前 `task_context_task_id`。处理：当前 task context 必须与 active lease/evidence task 一致，不一致返回 `invalid_contract`，并补回归。
- PR guardian 第四轮 `REQUEST_CHANGES`：
  - P1：active invalidation 缺失 `task_id` / `lease_id` 被误判为普通 rejected。处理：缺失 active execution binding 字段返回 `invalid_contract`，并补回归。
  - P1：active invalidation 只按字符串判断 `resource_id`，可能把 proxy 误当 account evidence 绑定。处理：校验 evidence 必须绑定 active lease 内真实 `account` resource，并补 account+proxy proxy 误绑回归。
- PR guardian 第五轮 `REQUEST_CHANGES`：
  - P2：active invalidation 在进入 FR-0010 `release()` 前读取 lifecycle store，可能泄漏裸 store/snapshot 异常。处理：预检读取失败归一化为 `runtime_contract/resource_state_conflict` failed envelope，并补回归。
- PR guardian 第六轮 `REQUEST_CHANGES`：
  - P1：active lease lookup miss 会把 context-mismatched evidence 降级为普通 rejected。处理：先校验 evidence task 与当前 task context，一致后若无 active lease 才返回 pre-admission rejected；若存在同 lease 的历史 truth 且绑定不一致，返回 `invalid_contract`。
  - P1：非 `ResourceLifecycleContractError` store 读取异常仍会泄漏。处理：预检读取复用 `load_snapshot_from_store()`，任意 backend failure 归一化为 `runtime_contract/resource_state_conflict`，并补回归。
- PR guardian 第七轮 `REQUEST_CHANGES`：
  - P2：脱敏校验把 `token/cookie/header` 字段名本身误判为泄漏。处理：reason / diagnostic_ref 允许已脱敏字段族诊断，只拒绝赋值形态或 raw/leaked/unredacted/secret marker，并补 `token expired`、`cookie expired`、`header signature invalid` 回归。
- PR guardian 第八轮 `REQUEST_CHANGES`：
  - P1：非 health-gated admission 仍消费无关 malformed evidence。处理：只有 `require_fresh_account_session=true` 且请求 `account` slot 时才 coerce/validate evidence；proxy-only 或显式 non-gated account admission pass-through，并补回归。
  - P1：`operation` 绑定不闭合。处理：health-gated admission 要求 evidence.operation 必须绑定当前 operation；active invalidation helper 新增当前 operation 参数并校验 missing/mismatch 为 `invalid_contract`，并补回归。
- PR guardian 第九轮 `REQUEST_CHANGES`：
  - P1：`evidence.operation=None` 仍可通过 health-gated admission 或 active invalidation。处理：当前 operation 与 evidence.operation 必须同时存在且相等，否则 `invalid_contract`；补 admission / invalidation 回归。
- PR guardian 第十轮 `REQUEST_CHANGES`：
  - P1：`evidence.adapter_key` / `evidence.capability` 缺失仍可通过 health-gated admission 或 active invalidation。处理：adapter/capability 与 operation 一样作为必填 execution-slice binding，缺失或不一致均 `invalid_contract`；补 admission / invalidation 回归。
- PR guardian 第十一轮 `REQUEST_CHANGES`：
  - P1：`evidence.task_id` 缺失仍可通过 health-gated admission。处理：health-gated admission 要求 evidence.task_id 必须绑定当前 task，缺失或不一致均 `invalid_contract`，并补回归。
  - P2：lease lookup miss 时缺失 adapter/capability 被降级为 ordinary rejected。处理：active invalidation 在读取 lifecycle 前统一校验 task/lease/bundle/adapter/capability/operation active-context 必填字段，缺失均 `invalid_contract`，并补回归。
- Review discipline correction：第十一轮后停止把 guardian 当探测器，改为本地 root-cause audit，统一收敛 health-gated admission 与 active invalidation 的 execution-slice binding 策略：task / adapter / capability / operation 必填且匹配当前 context；active invalidation 额外要求 lease / bundle 必填且绑定 active account resource。
- Final merge gate blocked：
  - P1：wrong `lease_id` 但 `resource_id` 仍被其他 active lease 占用时，被误降级为 ordinary rejected。处理：lease lookup miss 后继续检查同 resource active lease，若存在 active 占用则返回 `invalid_contract`，并补回归。
  - P2：invalidation fallback decision 把 evidence `observed_at` 冒充 decision `evaluated_at`。处理：fallback decision 使用实际 evaluation time `now_rfc3339_utc()`，并补回归。
- Final merge gate follow-up：
  - P1：相同 `observed_at` 的 healthy / stale / invalid evidence 按输入顺序影响 admission。处理：相同 observed_at 下按 health severity 稳定选择 `invalid > stale > healthy`，确保同一事实集 deterministic 且 fail-closed，并补回归。
  - P2：checkpoint 记录未追溯 live review head。处理：将验证记录更新为当前代码 checkpoint，并用 metadata-only follow-up 记录该 checkpoint。
- Final merge gate follow-up 2：
  - P1：admission 未把 evidence `resource_id` 纳入当前选中 account context。处理：health-gated admission 中所有 evidence 必须绑定当前选中 account resource；foreign-resource evidence 单独出现或混入合法 evidence 均返回 `invalid_contract`，并补回归。
- Final merge gate follow-up 3：
  - P1：malformed `observed_at` / `expires_at` / `evaluated_at` 泄漏 lifecycle exception。处理：resource health 边界统一把 RFC3339 解析错误收敛为 `ResourceHealthContractError`；admission 与 active invalidation 均返回 `invalid_contract`，并补回归。
- Final merge gate follow-up 4：
  - P1：no-active-lease fallback 未校验 evidence resource 是否存在且属于 account。处理：active lease miss 时先校验 resource 存在且为 account，否则 `invalid_contract`；补 missing resource 与 proxy resource 回归。

## 未决风险

- health evidence 被误写成第二套 resource lifecycle status。
- pre-admission invalid evidence 绕过 active lease 直接改写库存资源。
- unredacted diagnostic 泄漏 credential/session 私有字段。

## 回滚方式

- 使用独立 revert PR 回滚 `syvert/resource_health.py`、runtime tests 与本 exec-plan；FR-0387 formal spec 保留。

## 最近一次 checkpoint 对应的 head SHA

- `06ec07f1a65a660e7611d0c9de174a8d488c28af`
- Current HEAD may include a metadata-only checkpoint follow-up that records this verified implementation checkpoint.
