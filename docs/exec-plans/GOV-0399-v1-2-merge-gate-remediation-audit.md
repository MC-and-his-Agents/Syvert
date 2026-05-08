# GOV-0399 v1.2 Merge Gate Remediation Audit

## 关联信息

- Issue：`#399`
- item_key：`GOV-0399-v1-2-merge-gate-remediation-audit`
- item_type：`GOV`
- release：`v1.2.0`
- sprint：`2026-S24`
- Parent Phase：`#380`
- Parent FR：`#387`
- 上游 closeout Work Item：`#396`
- 关联 decision：docs/decisions/ADR-GOV-0399-v1-2-merge-gate-remediation-audit.md
- active 收口事项：`GOV-0399-v1-2-merge-gate-remediation-audit`
- 状态：`active`

## 目标

- 对 #395/#397/#398 未取得 guardian `APPROVE` / `safe_to_merge=true` 即合并的问题做可追溯 remediation audit。
- 降低代码质量风险：重点复核 #395 evidence/test/runtime truth，复核 #397/#398 release truth carrier。
- 修正审计发现的 stale release truth wording。
- 不重写 `v1.2.0` tag / GitHub Release；除非审计证明发布锚点或 runtime 存在严重缺陷。

## 范围

- 本次纳入：
  - `docs/exec-plans/GOV-0399-v1-2-merge-gate-remediation-audit.md`
  - `docs/exec-plans/artifacts/GOV-0399-v1-2-merge-gate-remediation-audit.md`
  - v1.2.0 release / sprint / GOV-0396 evidence carrier 中过期阶段 B wording 的 metadata hotfix
- 本次不纳入：
  - runtime carrier 语义修改
  - consumer boundary 语义修改
  - `v1.2.0` tag / GitHub Release rewrite
  - 新的 release closeout

## 违规事实

- PR `#395` merged at `eaec42d70ed432b7334eab19ef5ec5f69544f855` without a latest guardian `APPROVE` / `safe_to_merge=true` verdict.
- PR `#397` merged at `55ad1e5d336907fac6a990bd1742a6e351b92b97` without a latest guardian `APPROVE` / `safe_to_merge=true` verdict.
- PR `#398` merged at `4144d20c9740ada94b0bc213db5842b464b07e4b` without a latest guardian `APPROVE` / `safe_to_merge=true` verdict.
- Root process error：guardian stall was incorrectly treated as a reason to use local review as merge permission. Correct behavior is fail-closed and open remediation / tooling work.

## 违规判定来源

Audit command used for each PR:

- `gh pr view <pr> --json number,mergedAt,mergeCommit,reviews,comments,url`

The reproducible source chain is:

| PR | Merge time | Merge commit | PR review records | Pre-merge local-review source |
| --- | --- | --- | --- | --- |
| `#395` | `2026-05-08T15:40:24Z` | `eaec42d70ed432b7334eab19ef5ec5f69544f855` | `reviews=[]` | `https://github.com/MC-and-his-Agents/Syvert/pull/395#issuecomment-4407714609` records that `pr_guardian.py merge-if-safe 395 --refresh-review --delete-branch` was stopped after 2+ minutes with 0% CPU/no output and that merge readiness was based on local changed-file review and validation evidence. |
| `#397` | `2026-05-08T15:47:57Z` | `55ad1e5d336907fac6a990bd1742a6e351b92b97` | `reviews=[]` | `https://github.com/MC-and-his-Agents/Syvert/pull/397#issuecomment-4407767118` records a local release closeout review and merge-ready conclusion without a guardian verdict. |
| `#398` | `2026-05-08T15:53:00Z` | `4144d20c9740ada94b0bc213db5842b464b07e4b` | `reviews=[]` | `https://github.com/MC-and-his-Agents/Syvert/pull/398#issuecomment-4407801843` records a local published-truth review and merge-ready conclusion without a guardian verdict. |

Interpretation:

- The source commands expose no GitHub PR review records for #395/#397/#398.
- The pre-merge comments show local-review based merge readiness, not guardian `APPROVE` / `safe_to_merge=true`.
- #395 additionally records the failed guardian attempt before merge.
- Together these sources support the remediation conclusion that the merge gate was bypassed for all three PRs.

## 审计结论

- #395 runtime / evidence quality audit did not find a runtime correctness blocker.
- #395 replay tests rebuild the artifact from runtime behavior and compare it to the JSON evidence snapshot; they are not a pure hand-written assertion.
- High-risk runtime / consumer / evidence regressions passed: `Ran 383 tests`.
- #397/#398 release truth audit found stale wording in the final v1.2.0 release/sprint/GOV-0396 evidence carriers. This PR fixes the in-scope metadata defects and records the remaining historical GOV-0396 exec-plan wording as immutable prior-work truth that should not be edited from #399.
- No `v1.2.0` tag or GitHub Release rewrite is warranted by the current audit evidence.

## 验证摘要

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
- `python3 scripts/governance_gate.py --mode ci --base-sha <base> --head-sha <head> --head-ref issue-399-v1-2-0-merge-gate-remediation-audit`
  - 结果：通过。

## 最近一次 checkpoint 对应的 head SHA

- base：`4144d20c9740ada94b0bc213db5842b464b07e4b`
- 本 PR live head 由 PR `headRefOid` 与 guardian / merge gate 绑定。

## 后续约束

- 本 PR 合并前必须取得正常 merge gate。若 guardian 卡住，不得合并；应停在 PR 并记录 blocker。
- guardian stall / timeout / observability 应由独立治理 Work Item 修复，不在本 remediation audit 中顺手实现。

## 回滚方式

- 若 remediation carrier 或 wording hotfix 有误，使用独立 revert PR 撤销本事项修改。
- 若之后发现 runtime 缺陷，创建 HOTFIX Work Item 并按 patch release 流程处理。
