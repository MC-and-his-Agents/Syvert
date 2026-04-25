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
  - `docs/exec-plans/artifacts/CHORE-0158-operability-source-evidence.json`
  - `tests/runtime/render_operability_gate_artifact.py`
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
- `python3 -m py_compile syvert/operability_gate.py tests/runtime/render_operability_gate_artifact.py`
  - 结果：修复 artifact 重放入口后通过。
- `python3 -m unittest tests.runtime.test_operability_gate`
  - 结果：首轮通过，`Ran 10 tests`，`OK`；修复 guardian 一轮阻断后再次通过，`Ran 13 tests`，`OK`；修复 guardian 二轮阻断后再次通过，`Ran 17 tests`，`OK`；修复 guardian 三轮阻断后再次通过，`Ran 21 tests`，`OK`；修复 guardian 四轮阻断后再次通过，`Ran 23 tests`，`OK`；修复 guardian 五轮阻断后再次通过，`Ran 25 tests`，`OK`；修复 guardian 六轮阻断后再次通过，`Ran 28 tests`，`OK`；修复 guardian 七轮阻断后再次通过，`Ran 31 tests`，`OK`；修复 guardian 八轮阻断后再次通过，`Ran 34 tests`，`OK`；补齐 exact baseline / invalid-case summary / reviewable preconditions / artifact reproduction entrypoint 后再次通过，`Ran 37 tests`，`OK`；修复 guardian 九轮 snapshot 断言来源阻断后再次通过，`Ran 40 tests`，`OK`；改为消费 source evidence artifact 与 resolved `baseline_gate_result` 后再次通过，`Ran 43 tests`，`OK`；renderer 改为现场运行上游 evidence tests 后仍通过，`Ran 43 tests`，`OK`；补齐 `upstream_refs` revision 绑定与 non-HEAD render fail-closed 后再次通过，`Ran 45 tests`，`OK`；放宽 baseline/evidence ref grammar 与 gate-level metrics exact-value 后再次通过，`Ran 47 tests`，`OK`；收紧 baseline pass 现场执行、baseline ref revision、case policy/metrics 观测链与 concurrency failure metrics 后再次通过，`Ran 49 tests`，`OK`；source artifact 补齐 `baseline_gate_result` / `policy_snapshot` 并让 malformed source 结构化 fail-closed 后再次通过，`Ran 50 tests`，`OK`；补齐 FR-00070 近似伪造、缺 mandatory case、缺 case_id、缺 upstream_modules 回归后再次通过，`Ran 53 tests`，`OK`；补齐重复 case_id 与未批准 upstream module 回归后再次通过，`Ran 55 tests`，`OK`；补齐 source `actual_result` revision-bearing values、null `evidence_refs`、missing `policy_snapshot` 与 missing mandatory case summary 回归后再次通过，`Ran 58 tests`，`OK`；补齐非 `evidence:` ref 的 actual_result revision 绑定回归后再次通过，`Ran 59 tests`，`OK`；补齐 case-scoped evidence refs、approved upstream refs 与 missing-case failed_dimensions 回归后再次通过，`Ran 61 tests`，`OK`；补齐 source extra case / malformed JSON fail-closed 与 backed local evidence ref 回归后再次通过，`Ran 63 tests`，`OK`；补齐 forged baseline proof 与 fake local case proof slot 回归后再次通过，`Ran 65 tests`，`OK`。
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
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-05e540d.json`
  - 结果：`REQUEST_CHANGES`；指出 baseline ref substring forgery、summary 未反映 actual assertion failure、malformed expected values 可能抛异常，以及缺少 reviewable gate artifact。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-4f45b6f.json`
  - 结果：`REQUEST_CHANGES`；指出 case data 不得由 runtime builder 自证、side effects / forbidden mutations 未求值、case verdict 未由 validator 回写。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-c5b90b7.json`
  - 结果：`REQUEST_CHANGES`；指出 baseline ref 未绑定 `v0.6.0`，以及 case-scoped metadata failure 未回写到 case verdict / summary。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-b62abb9.json`
  - 结果：`REQUEST_CHANGES`；指出 `!= ""` 与 path-to-path equality 对缺字段未 fail-closed，以及 `failure_log_metrics` side-effect 证据需贴合 FR-0019 canonical matrix。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-46cafc5.json`
  - 结果：`REQUEST_CHANGES`；指出 mandatory `forbidden_mutations` 未冻结校验、扩展 case entrypoints 未白名单、evidence ref 校验过宽。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-b893635.json`
  - 结果：`REQUEST_CHANGES`；指出 case-local policy / metrics 不得被顶层 snapshot 覆盖、revision evidence 绑定不能用子串、`actual_result_ref` 需要受控 evidence 格式。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-32c4288.json`
  - 结果：`REQUEST_CHANGES`；指出 `baseline_gate_ref` 必须精确绑定 `FR-0007:version_gate:v0.6.0:baseline:<execution_revision>`、invalid/missing case 不能从 summary 消失、generated matrix case 不能使用占位 preconditions、artifact 需要本地重放入口。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-9484a36.json`
  - 结果：`REQUEST_CHANGES`；指出 case-level `actual_result.policy` / `actual_result.metrics` 不能自证 snapshot 断言，`policy.*` / `metrics.*` 必须绑定顶层 normalized `policy_snapshot` / `metrics_snapshot`。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-2956afc.json`
  - 结果：`REQUEST_CHANGES`；指出 artifact renderer 不能由 frozen expected_result 与 hard-coded metrics 自造 pass 结果，`baseline_gate_ref` 也不能只校验字符串形状，必须消费 resolved FR-0007 baseline pass evidence。

- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-8aebf2b.json`
  - 结果：`REQUEST_CHANGES`；指出 renderer 不能对 cached evidence 做 SHA 替换，也不能从静态 fixture 复制后丢失 `upstream_refs`，必须现场解析上游 evidence 并在 `OperabilityGateResult` 中保留可复验引用。

- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-65c1741.json`
  - 结果：`REQUEST_CHANGES`；指出 FR-0007 baseline 不能由 fixture 自造，case `upstream_refs` 必须绑定 `execution_revision` 并进入全局 evidence 校验，renderer 显式 `--execution-revision` 不能与 HEAD 混用，PR body 需要补齐 scope / validation / risk / rollback。

- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-4c40108.json`
  - 结果：`REQUEST_CHANGES`；指出 baseline/evidence ref grammar 不得过度收紧为私有前缀，gate-level metrics counters 不得把可扩展字段固定为 0。

- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-12444c4.json`
  - 结果：`REQUEST_CHANGES`；指出 renderer 不能写死 baseline pass，`baseline_gate_ref` 本身必须绑定 revision，case `policy.*` / `metrics.*` 断言必须来自 case 观测，`concurrency_case_failure_total` 至少覆盖 rejection path。

- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-a9965ac.json`
  - 结果：`REQUEST_CHANGES`；指出 renderer 必须从 source artifact 消费 resolved baseline gate result，source artifact 缺 `cases` / `policy_snapshot` / `metrics_snapshot` / baseline 时必须结构化 fail-closed，不能抛 `KeyError` 或默认补齐。

- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-f07a026.json`
  - 结果：`REQUEST_CHANGES`；指出 `baseline_gate_ref` 需拒绝 `FR-00070` 近似编号伪造，source evidence 缺 mandatory case / `case_id` / `upstream_modules` 时必须结构化 fail-closed。

- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-f5e34e7.json`
  - 结果：`REQUEST_CHANGES`；指出提交内 gate artifact revision 滞后当前 PR HEAD、case-level upstream 模块需限制为实际执行且批准集合、source evidence 重复 `case_id` 必须 fail-closed。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-f2607c6.json`
  - 结果：`REQUEST_CHANGES`；指出版本化 gate result 无法绑定 live PR head，且 case-level `evidence_refs` 不能由 renderer 自造，必须来自 source evidence 并缺失时 fail-closed。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-2990ebd.json`
  - 结果：`REQUEST_CHANGES`；指出 source `actual_result` 中 revision-bearing values 仍可缓存旧 revision、case `evidence_refs: null` 未 fail-closed、缺失 `policy_snapshot` 会默认补齐、缺 mandatory case 未进入 `summary.failed_case_ids`。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-3179a94.json`
  - 结果：`REQUEST_CHANGES`；指出 `actual_result` revision 绑定只覆盖 `evidence:` 前缀，`operability:` / `tests:` 等已接受 revision-bearing ref 仍可携带旧 revision 并 pass。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-6d46182.json`
  - 结果：`REQUEST_CHANGES`；指出 case-level `actual_result_ref` / `evidence_refs` 只做形状校验，未证明归属于当前 `case_id` 或批准上游模块；同时 missing mandatory case / dimension 的 fail-closed summary 未回写 `failed_dimensions`。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-f1748b6.json`
  - 结果：`REQUEST_CHANGES`；指出 renderer 会丢弃 source artifact 中的额外 case、source artifact 读/解析失败会直接抛异常，以及 case-level evidence refs 仍可用未背书的 synthetic refs 自证。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 252 --post-review --json-output /tmp/syvert-guardian-252-2e5be2c.json`
  - 结果：`REQUEST_CHANGES`；指出 `baseline_gate_result.evidence_refs` 可由任意 revision-matched local ref 伪造，case-local refs 只校验文件存在、未校验真实证据槽位。
- `docs/exec-plans/artifacts/CHORE-0158-operability-source-evidence.json`
  - 结果：已新增 source evidence artifact，作为 renderer 输入，包含 resolved `baseline_gate_result`、metrics snapshot、policy snapshot、case-level `actual_result_ref` / `evidence_refs` / `actual_result` / `upstream_modules`；renderer 现场运行 `tests.runtime.test_execution_control`、`tests.runtime.test_runtime_observability`、`tests.runtime.test_http_api`、`tests.runtime.test_cli_http_same_path`、`tests.runtime.test_version_gate` 作为上游 evidence，并保留 case-level `upstream_refs`；source artifact 只保存不含具体 commit revision 的观测事实，`actual_result` 中需要绑定 revision 的 evidence values 使用 `{revision}` 占位并在 render 时物化，validator 会拒绝与 `execution_revision` 不一致的 values。
- `python3 -m tests.runtime.render_operability_gate_artifact --execution-revision $(git rev-parse HEAD)`
  - 结果：通过，输出 `/tmp/CHORE-0158-operability-gate-result.json` 与 `verdict=pass cases=20 execution_revision=<当前 HEAD>`；generated gate result 不再进入版本控制，避免 commit SHA 自引用导致 artifact 永远滞后 live PR head。

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
- 当前可恢复 checkpoint：以 PR live head 的 `git rev-parse HEAD` 为准；包含 gate runner、mandatory matrix validator、revision/evidence 绑定校验、case-level evidence fail-closed、allowed dimension / entrypoints 校验、baseline ref / release / execution_revision 精确绑定校验、resolved FR-0007 `baseline_gate_result` pass evidence 校验、case-scoped metadata failure attribution、invalid case summary reconciliation、reviewable case preconditions、artifact 本地重放入口、source evidence artifact consumption、renderer 现场运行上游 unittest evidence、generated gate result 不入库、upstream_refs revision binding、non-HEAD render fail-closed、contract-approved evidence ref grammar、extensible metrics counters、baseline runtime execution result、case policy/metrics observation required、concurrency failure metrics minimum、complete source evidence validation、malformed source fail-closed、near-FR baseline forgery rejection、case-level source completeness checks、approved upstream module set、duplicate source case rejection、local evidence ref format / actual_result_ref 校验、token-level revision matching、case-local metrics / policy evidence 校验、顶层 normalized `policy_snapshot` / `metrics_snapshot` 断言来源绑定、gate/matrix identity freeze、actual_result 断言求值、missing field fail-closed、canonical `failure_log_metrics` side-effect evidence、side effects / forbidden mutations 机判校验、mandatory forbidden mutations freeze、case verdict validator 回写、summary failure reconciliation、malformed expected value fail-closed、专项测试与验证证据；后续若只更新 review / merge gate / closeout metadata，不推进新的 runtime 语义 checkpoint。
