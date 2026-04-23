# CHORE-0157-fr-0019-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0157-fr-0019-formal-spec-closeout`
- Issue：`#233`
- item_type：`CHORE`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：`docs/specs/FR-0019-v0-6-operability-release-gate/`
- 关联 PR：`#243`
- 状态：`active`
- active 收口事项：`CHORE-0157-fr-0019-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0019` formal spec 套件，冻结 `v0.6.0` 可运维发布门禁与回归矩阵，并把后续实现明确交给 `#234` release gate matrix implementation，再由 `#235` parent closeout 收口。

## 规范性依赖

- `FR-0016`：本次 closeout 必须把默认 policy、retryable predicate、`execution_timeout` 控制码、pre/post accepted 并发拒绝语义写成字段级 gate 预期。
- `FR-0017`：本次 closeout 必须把 failure/log/metrics/refs 的结构化字段要求写入矩阵 contract。
- `FR-0018`：本次 closeout 必须把 HTTP submit/status/result 与 CLI run/query 同 Core path 的证明要求写入矩阵 contract。

## 范围

- 本次纳入：
  - `docs/specs/FR-0019-v0-6-operability-release-gate/`
  - `docs/exec-plans/FR-0019-v0-6-operability-release-gate.md`
  - `docs/exec-plans/CHORE-0157-fr-0019-formal-spec-closeout.md`
- 本次不纳入：
  - `syvert/**`
  - `tests/**`
  - `scripts/**`
  - `docs/releases/**`
  - `docs/sprints/**`
  - `FR-0007` 正文或既有版本 gate 语义改写
  - release closeout、tag、GitHub Release
  - 外部 SaaS 监控、生产验收、分布式压测

## 当前停点

- `issue-233-fr-0019-formal-spec` worktree 已用于 `#233` formal spec closeout。
- 当前回合只允许修改 `FR-0019` formal spec 套件与两个 exec-plan。
- 已完成初版 formal spec、plan、risks、data-model、contracts README 与两个 exec-plan 的落盘，并已 rebase 到包含 `#237`、`#239`、`#241` 的 `origin/main`。
- 当前停点是把 live review head 之前的 semantic checkpoint `10a767c0cd473651348f868ba88dcb5210fe11ad` 与验证证据回写到 exec-plan，使当前 head 只承担 review-sync。

## 下一步动作

- 回写 semantic checkpoint `10a767c0cd473651348f868ba88dcb5210fe11ad` 对应的 guard 结果与 checkpoint 元数据，确保验证结论覆盖当前语义。
- 等待 `#243` 当前 review-sync head 的 required checks 完成后运行 guardian。
- 若 guardian 通过，则按受控入口合并 `#243`，并核对主干真相、远端分支删除与 issue/project 状态。
- spec review 通过后，由 `#234` 进入 release gate matrix implementation；`#235` 继续 parent closeout。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 冻结 operability release gate 与回归矩阵，使 release gate matrix implementation 可以围绕 timeout / retry / concurrency、failure / log / metrics、HTTP submit / status / result、CLI / API same-path 建立同一套可复验门禁。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0019` 的 formal spec closeout Work Item。
- 阻塞：
  - 若 `#233` 未完成 spec review，`#234` 不得进入 implementation。
  - 若 `#234` 未完成实现与门禁证据，`#235` 不得 parent closeout。
  - 若文档误把 `#233` 扩张成 release closeout / tag / GitHub Release，将违反当前 Work Item 边界。

## 已验证项

- 已核对 `AGENTS.md`、`WORKFLOW.md`、`spec_review.md`、`docs/specs/README.md`。
- 已核对 formal spec 模板：`docs/specs/_template/spec.md`、`docs/specs/_template/plan.md`、`docs/specs/_template/risks.md`、`docs/specs/_template/data-model.md`。
- 已核对参考 spec：`FR-0007`、`FR-0008`、`FR-0009`、`FR-0015`。
- `git rebase origin/main`
  - 结果：已将当前 checkpoint 重放到包含 `#237`、`#239`、`#241` 的 `origin/main`，确保 `FR-0016`、`FR-0017`、`FR-0018` 依赖以主干真相为准。
- 已按本事项要求对齐 `FR-0016`、`FR-0017`、以及已合入 `origin/main` 的 `FR-0018` / `#241` 语义，并同步到 `FR-0019` gate matrix 字段级断言。
- 已核对参考 exec-plan：`docs/exec-plans/CHORE-0138-fr-0013-formal-spec-closeout.md`。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：已确认 semantic checkpoint `10a767c0cd473651348f868ba88dcb5210fe11ad` 通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：已确认 semantic checkpoint `10a767c0cd473651348f868ba88dcb5210fe11ad` 通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：已确认 semantic checkpoint `10a767c0cd473651348f868ba88dcb5210fe11ad` 通过。
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-233-fr-0019-formal-spec`
  - 结果：已确认 semantic checkpoint `10a767c0cd473651348f868ba88dcb5210fe11ad` 通过。
- `python3 scripts/open_pr.py --class spec --issue 233 --item-key CHORE-0157-fr-0019-formal-spec-closeout ...`
  - 结果：已创建 formal spec PR `#243`，进入受控 review / CI / merge gate 链路。

## 未决风险

- 若 reviewer 要求 HTTP contract 固定更具体的 endpoint shape，需要确认是否仍属于 formal spec 层，避免提前绑定实现框架。
- 若 `#234` 使用抽象同义词而非字段级断言实现 matrix case，将导致 FR-0016/17/18 语义无法自动化验收。
- 若后续 `#234` 发现现有 runtime 缺少可构造 timeout / concurrency case 的测试 seam，应在实现 PR 中补测试 seam，而不是回写本 Work Item 的实现代码。
- 若 GitHub 状态字段与仓内 exec-plan 不一致，应以 GitHub 为调度真相、repo 为语义真相分别收口，不能在 repo 内创建状态镜像。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `FR-0019` formal spec 套件与两个 exec-plan 的文档增量，不回退其他 Work Item、相邻 FR 或 runtime 变更。

## checkpoint 记录方式

- semantic checkpoint：`10a767c0cd473651348f868ba88dcb5210fe11ad`，对应 retry 预算语义、`execution_revision` / `metrics_snapshot` gate result contract，以及 pre-admission observability 字段收口后的 formal spec 语义基线。
- review-sync follow-up：后续若只回写当前受审 PR、门禁或审查元数据，只作为 metadata-only follow-up，不伪装成新的语义 checkpoint。

## 最近一次 checkpoint 对应的 head SHA

- `10a767c0cd473651348f868ba88dcb5210fe11ad`
