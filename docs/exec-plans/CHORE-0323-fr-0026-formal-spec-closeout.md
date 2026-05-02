# CHORE-0323-fr-0026-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0323-fr-0026-formal-spec-closeout`
- Issue：`#323`
- item_type：`CHORE`
- release：`v0.8.0`
- sprint：`2026-S21`
- 关联 spec：`docs/specs/FR-0026-adapter-provider-compatibility-decision/`
- 关联 decision：
- 关联 PR：`#333`
- active 收口事项：`CHORE-0323-fr-0026-formal-spec-closeout`
- 状态：`active`

## 目标

- 创建并收口 `FR-0026` formal spec 套件，冻结 `AdapterCapabilityRequirement x ProviderCapabilityOffer -> AdapterProviderCompatibilityDecision` 的输入、输出、状态、错误 carrier、fail-closed 与 no-leakage 语义，为 `#324/#325/#326/#327` 提供 implementation-ready formal input。

## 范围

- 本次纳入：
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/spec.md`
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/plan.md`
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/data-model.md`
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/contracts/README.md`
  - `docs/specs/FR-0026-adapter-provider-compatibility-decision/risks.md`
  - `docs/exec-plans/CHORE-0323-fr-0026-formal-spec-closeout.md`
  - 必要的 `docs/releases/v0.8.0.md` 与 `docs/sprints/2026-S21.md` 索引入口
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `.github/**`
  - runtime compatibility decision、no-leakage guard、docs evidence、adapter implementation、manifest validator 或 contract test 实现
  - 既有 `FR-0023`、`FR-0024`、`FR-0025` 或 `FR-0027` formal spec 修改
  - requirement carrier、offer carrier 或 resource profile carrier 本体
  - provider selector、priority、fallback、routing、marketplace 或真实 provider 产品支持
  - Core provider discovery / routing
  - 关闭父 FR `#298`

## 当前停点

- worktree：`/Users/mc/code/worktrees/syvert/issue-323-fr-0026-compatibility-decision-formal-spec`
- 分支：`issue-323-fr-0026-compatibility-decision-formal-spec`
- 原始 worktree 创建基线：`e456547dd4bc8145e7a1c77be1e89164a7d33fc8`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`docs/AGENTS.md`、`docs/process/delivery-funnel.md`、`spec_review.md`、`FR-0024`、`FR-0025`、`FR-0027`、父 FR `#298` 与 Work Item `#323` GitHub truth。
- 当前 checkpoint：已创建 `FR-0026` formal spec 套件、active exec-plan 与 release/sprint 索引入口；PR `#333` 已通过受控入口创建并绑定 `Fixes #323`。guardian 前四轮均返回 `REQUEST_CHANGES`，当前已 rebase 到最新 `origin/main` 消除 stale-base implementation diff，并修正 no-leakage carrier 边界、`invalid_contract` evidence / adapter / capability / execution mismatch 可构造性、observability 冲突值语义、GWT trailing whitespace 与 checkpoint SHA 漂移，待提交本轮修正、重跑 gates、guardian、merge 与 closeout。

## 下一步动作

- 完成 spec review / guardian review、GitHub checks 与受控 merge。
- 合入后确认 `#323` closeout，更新父 FR `#298` GitHub comment，清理 worktree 并退役分支。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.8.0` 把 Adapter + Provider compatibility decision 从路线图目标推进为可审查、可验证、可被 runtime / guard / docs / closeout 消费的 formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S21` 中 `FR-0026` 的 formal spec closeout Work Item。
- 阻塞：
  - `#324` compatibility decision runtime 需要本 carrier 作为实现目标。
  - `#325` provider no-leakage guard 需要本 no-leakage contract 作为校验目标。
  - `#326` docs / evidence 需要本 decision 解释边界作为文档目标。
  - `#327` 父 FR closeout 需要本 spec、runtime、guard、docs / evidence 与 GitHub 状态主干事实。

## 已验证项

- `python3 scripts/create_worktree.py --issue 323 --class spec`
  - 结果：通过，创建 worktree `issue-323-fr-0026-compatibility-decision-formal-spec`
- `gh api user --jq .login`
  - 结果：通过，确认本机 `gh` keyring 可用，登录用户为 `mcontheway`
- 已核对 `AGENTS.md`、`WORKFLOW.md`、`docs/AGENTS.md`、`docs/process/delivery-funnel.md`、`spec_review.md`。
- 已核对 `#323` GitHub truth：item_key=`CHORE-0323-fr-0026-formal-spec-closeout`，item_type=`CHORE`，release=`v0.8.0`，sprint=`2026-S21`，integration fields 为 `none/no/local_only`。
- 已核对父 FR `#298`：目标为冻结 Adapter requirement x Provider offer -> compatibility decision，明确不定义 requirement / offer carrier 本体，不引入 selector、priority、fallback、排序、打分或真实 provider 产品支持。
- 已核对 `FR-0024`：`AdapterCapabilityRequirement` 是 Adapter-side decision input，合法 requirement 不等于 compatibility approved。
- 已核对 `FR-0025`：`ProviderCapabilityOffer` 是 Provider-side decision input，合法 offer 不等于 compatibility approved，Provider offer 不进入 Core discovery / routing。
- 已核对 `FR-0027`：resource profile tuple、matcher `one-of`、proof binding 与 adapter coverage 是 resource profile truth，本 FR 只消费。
- `git commit -m 'docs(spec): 收口 FR-0026 兼容性判断规约'`
  - 结果：已生成 formal spec 语义 checkpoint `23e8eb810dbbcfe71411036fcc29ab8cf3804dcf`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-323-fr-0026-compatibility-decision-formal-spec`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class spec --base-ref origin/main --head-ref HEAD`
  - 结果：通过，PR class=`spec`，变更类别=`docs, spec`
- `git push -u origin issue-323-fr-0026-compatibility-decision-formal-spec`
  - 结果：首次因 GitHub HTTPS `SSL_ERROR_SYSCALL` 失败，重试通过；远端分支已创建并设置 upstream
- `python3 scripts/open_pr.py --class spec --issue 323 --item-key CHORE-0323-fr-0026-formal-spec-closeout --item-type CHORE --release v0.8.0 --sprint 2026-S21 --title 'docs(spec): 收口 FR-0026 compatibility decision formal spec' --closing fixes --integration-touchpoint none --shared-contract-changed no --integration-ref none --external-dependency none --merge-gate local_only --contract-surface none --joint-acceptance-needed no --integration-status-checked-before-pr no --integration-status-checked-before-merge no`
  - 结果：已创建当前受审 spec PR `#333 https://github.com/MC-and-his-Agents/Syvert/pull/333`
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 333 --post-review --json-output /tmp/syvert-pr-333-guardian.json`
  - 结果：首次返回 `REQUEST_CHANGES`。阻断项：decision data model 中 `provider_key` 顶层/observability 与 no-leakage 冲突；`invalid_contract` 在 proof refs 为空时无法满足 evidence 非空约束；GWT 行尾空白。
- 已修正：
  - `AdapterProviderCompatibilityDecision` 顶层字段与 `CompatibilityDecisionObservability` 不再携带 `provider_key` / `offer_id`。
  - provider identity 只允许出现在 `CompatibilityDecisionEvidence.adapter_bound_provider_evidence`，并明确 Core-facing projection 不得嵌入完整 Adapter-bound evidence。
  - `resource_profile_evidence_refs` 只记录已解析 proof refs；`invalid_contract` 可通过 `invalid_contract_evidence` 表达空 refs、重复 refs、不可解析或不唯一 refs。
  - `git diff --check` 已对当前工作区通过。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 333 --post-review --json-output /tmp/syvert-pr-333-guardian.json`
  - 结果：第二次返回 `REQUEST_CHANGES`。阻断项：当前分支未包含最新 `origin/main`，导致两点 diff 误显示删除 `#315` implementation truth；adapter mismatch 时 `adapter_key` 字段不可构造；requirement / offer evidence 缺失时 `invalid_contract` evidence 不可构造。
- 已修正：
  - `git fetch origin main` 后 `git rebase origin/main` 成功，`origin/main..HEAD` 与 `origin/main...HEAD` 均只包含 #323 ownership 文件。
  - adapter key 缺失或不一致时，decision 顶层 `adapter_key=null`，冲突值进入 `invalid_contract_evidence.observed_values`。
  - requirement / offer evidence refs 在 `invalid_contract` 且缺失、不可解析或不唯一时可以为空，不得伪造占位 ref。
  - 当前工作区 `spec_guard`、`docs_guard` 与 `git diff --check` 已通过。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 333 --post-review --json-output /tmp/syvert-pr-333-guardian.json`
  - 结果：第三次返回 `REQUEST_CHANGES`。阻断项：capability / execution slice mismatch、missing fixed fields 或 approved slice 越界时，`capability` 与 `execution_slice` 字段不可构造；rebase 后 exec-plan 仍记录旧不可解析 semantic checkpoint SHA。
- 已修正：
  - capability 缺失、不一致或越界时，decision 顶层 `capability=null`，冲突值进入 `invalid_contract_evidence.observed_values`。
  - execution slice 缺失、不一致或越界时，decision 顶层 `execution_slice=null`，冲突值进入 `invalid_contract_evidence.observed_values`。
  - rebase 后 checkpoint SHA 已替换为当前历史可解析提交。
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 333 --post-review --json-output /tmp/syvert-pr-333-guardian.json`
  - 结果：第四次返回 `REQUEST_CHANGES`。阻断项：observability 在 adapter / capability / execution 冲突场景仍缺少 null / omission 语义；exec-plan 当前停点与验证记录未同步到第三轮 guardian-fix 状态。
- 已修正：
  - `CompatibilityDecisionObservability` 在 `invalid_contract` 且 adapter key、capability 或 execution slice 缺失、不一致或越界时，对应字段必须为 `null` 或省略，冲突摘要只能进入 `invalid_contract_evidence.observed_values`。
  - active exec-plan 当前停点与待验证项已同步为第四轮 guardian-fix 后状态。

## 待验证项

- 提交当前 observability / exec-plan 修正后复跑本地 gates、guardian review、GitHub checks、受控 merge 与 issue closeout。

## 未决风险

- 若后续 `#324/#325/#326` 在未消费本 spec 的情况下实现自己的 decision shape，会形成 runtime / guard / docs 三套 truth。
- 若后续实现把 `matched` 扩写为 provider selector、priority、fallback 或 Core routing，会破坏 Core / Adapter / Provider 边界。
- 若 provider key 泄漏到 Core registry、TaskRecord、routing 或 resource lifecycle，会把 Adapter-bound Provider 概念升格为 Core provider contract。

## 回滚方式

- 使用独立 revert PR 撤销 `docs/specs/FR-0026-adapter-provider-compatibility-decision/`、本 exec-plan 与 release/sprint 索引增量。
- 若需要改变 decision 边界，必须先回到父 FR `#298` 更新 GitHub truth，不得在后续 implementation PR 中隐式改写。

## 最近一次 checkpoint 对应的 head SHA

- worktree 创建基线：`e456547dd4bc8145e7a1c77be1e89164a7d33fc8`
- rebase 后 formal spec 语义 checkpoint：`3dac353e5d59d567ebc08224b5baf5468122ae61`
