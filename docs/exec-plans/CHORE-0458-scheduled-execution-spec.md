# CHORE-0458 Scheduled Execution formal spec admission

## 关联信息

- item_key：`CHORE-0458-scheduled-execution-spec`
- Issue：`#458`
- item_type：`CHORE`
- release：`unbound`
- sprint：`unbound`
- Parent Phase：`#456`
- Parent FR：`#457`
- 关联 spec：`docs/specs/FR-0457-scheduled-execution-core-contract/`
- 关联 artifact：`docs/exec-plans/artifacts/CHORE-0458-scheduled-execution-fixture-inventory.md`
- spec review：`docs/specs/FR-0457-scheduled-execution-core-contract/spec-review.md`
- 状态：`active`

## 目标

- Work Item：`#458`
- Parent FR：`#457`
- Scope：完成 `v1.6.0` post-release truth audit residual cleanup，并为 Scheduled Execution 建立 formal spec admission，明确延迟 / 周期触发必须复用现有 Core 主路径。
- Out of scope：runtime carrier、due-task worker、scheduler service、consumer migration、evidence replay、release closeout、UI、BI、上层 workflow、write-side、provider selector/fallback/marketplace。

## 改动记录

- 核对 `v1.6.0` GitHub Phase / FR / Work Item、annotated tag、GitHub Release、release index、sprint index 与 roadmap truth。
- 将已完成的 `#446/#448/#449/#450` GitHub issue body `execution_status` 修正为 `completed`。
- 修正 `docs/releases/v1.6.0.md` 与 `docs/sprints/2026-S25.md` 中 closeout pending / ready-to-close 的残留表述。
- 创建 Scheduled Execution admission 链：Phase `#456`、FR `#457`、formal spec Work Item `#458`。
- 建立 sanitized fixture / error / evidence inventory，供后续 runtime/evidence Work Item 使用。

## Scheduled Execution boundary

- Scheduled Execution 只定义 Core 何时 admission 和执行 delayed / recurring task request。
- scheduled target 必须复用现有 Core task path、TaskRecord、dataset、resource trace、timeout、retry 与 concurrency contract。
- schedule record 只表达触发时间、触发规则、目标任务请求与执行策略。
- 本 Work Item 不定义上层业务策略、自动运营 workflow、调度产品 UI、scheduler service、write-side operation 或 provider marketplace。

## 验证记录

- `gh issue view 444/445/446/447/448/449/450`：Batch / Dataset Phase、FR 与 Work Items 均为 completed，Work Item body `execution_status` 已对齐。
- `gh issue view 381`：Read-Side Capabilities Phase 已 closed/completed；`2026-S25` sprint index 中 `#381` 表述已对齐为 completed independent Phase。
- `gh release view v1.6.0 --json tagName,name,isDraft,isPrerelease,publishedAt,url,targetCommitish`：GitHub Release 指向 `357024e4389bb2f75b578f202c09bdb20222280e`，非 draft，非 prerelease。
- `git cat-file -t v1.6.0 && git rev-parse v1.6.0 && git rev-parse v1.6.0^{}`：`v1.6.0` 为 annotated tag，tag object `300b405c0835568fbd91c90a3715fa927ff2a883`，target `357024e4389bb2f75b578f202c09bdb20222280e`。
- `gh issue view 456/457/458`：Scheduled Execution Phase / FR / formal spec Work Item 可定位，release/sprint 未绑定，scope/non-goals/依赖/验证方式已写入。
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/workflow_guard.py --mode ci`
- `python3 scripts/version_guard.py --mode ci`
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
- `git diff --check origin/main...HEAD`
- `docs/specs/FR-0457-scheduled-execution-core-contract/spec-review.md`：formal spec admission review result recorded; implementation readiness remains blocked until later runtime Work Item admission.
- 结果：`spec_guard`、`docs_guard`、`workflow_guard`、`version_guard`、`governance_gate` 与 `git diff --check origin/main...HEAD` 均通过。

## 未决风险

- Scheduled Execution 的具体 release 与 sprint 未绑定；后续执行回合必须通过 release planning / sprint planning 显式决定。
- `#458` 只完成 admission 和 formal spec 准备，不证明 runtime 行为。
- 任何 runtime、scheduler service、consumer migration 或 evidence replay 必须拆成后续 Work Item。

## 回滚方式

- GitHub issue body truth 修正错误：再次使用 GitHub issue edit 回写正确状态。
- 仓内 truth 修正错误：使用独立 docs PR revert 本 Work Item 对 `docs/releases/v1.6.0.md`、`docs/sprints/2026-S25.md` 与本 exec-plan 的增量。
- Scheduled Execution admission 链错误：关闭或更新 `#456/#457/#458`，并保留 `#383` deferred/not planned 状态不变。

## 最近一次 checkpoint 对应的 head SHA

- `dfa04cd88ae185f40dcd147598308f6eb8e42a0f` on `issue-458-scheduled-execution-admission`
