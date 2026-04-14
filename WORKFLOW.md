---
tracker:
  kind: github
  scope: current-repo
workspace:
  root: $SYVERT_WORKSPACE_ROOT
  naming: issue-{number}-{slug}
agent:
  max_turns: 20
codex:
  thread_sandbox: workspace-write
  approval_policy: never
---

# Syvert Repo Workflow Contract

## 任务输入来源

- 任务来源固定为当前仓库的 GitHub Issues / Projects。
- 不从仓库内 Markdown 获取 backlog 或 sprint 状态，也不在仓库内维护 sprint 状态镜像。
- 每次执行需绑定事项上下文，并在 PR 中显式关联。
- GitHub 是单一调度层：负责 `Phase / FR / Work Item` 层级、状态、优先级、依赖、关闭语义与 Sprint / Project 排期。
- 仓库是单一语义层：负责 formal spec、exec-plan、风险、验证证据、checkpoint 与恢复上下文。
- 只有 GitHub Work Item 可以进入执行回合；Phase 与 FR 只作为上位容器，不直接创建 worktree 或承载执行 PR。
- 事项上下文最少包含：
  - `Issue`
  - `item_key`
  - `item_type`
  - `release`
  - `sprint`
- `Issue` 仍是任务状态真相源入口；`item_key`、`release`、`sprint` 是执行上下文字段，不替代 GitHub Issues / Projects。
- `Phase` 只承载阶段目标；`FR` 是 canonical requirement 容器；Work Item 是唯一执行入口。
- formal spec 默认绑定到 `FR`；`exec-plan` 默认绑定到当前 Work Item 执行回合。
- `docs/releases/` 与 `docs/sprints/` 只承载仓内聚合索引，不替代 GitHub Issues / Projects 的状态真相源。
- 新事项与存量事项在进入新的执行回合前都必须补齐完整事项上下文。
- 术语约定：
  - `新事项`：首次进入当前交付漏斗、且尚未在仓库内形成 active `exec-plan` 恢复工件的事项
  - `存量事项`：在本协议升级前已存在仓库内恢复工件，但尚未补齐事项上下文的事项
  - `长任务`：需要 `checkpoint -> resume -> handoff` 恢复能力，并因此必须维护 `exec-plan` 的执行回合

## worktree / bootstrap 规则

- worktree key 固定为 `issue-{number}-{slug}`。
- 优先通过 `python3 scripts/create_worktree.py --issue <n> --class <class>` 创建或复用工作区。
- 分支完成合入或确认被替代后，通过 `python3 scripts/retire_branch.py` 执行归档与退役。
- worktree key 仍仅由 `Issue` 生成；`item_key`、`release`、`sprint` 不改变现有 worktree 生成与复用机制。
- worktree 与执行分支只能绑定到当前 Work Item；不得直接为 Phase 或 FR 创建执行现场。
- `item_type` 当前约定为：`FR` / `HOTFIX` / `GOV` / `CHORE`。
- `item_key` 固定命名为 `<item_type>-<4-digit>-<slug>`，例如：`FR-0123-content-detail-runtime`、`GOV-0007-release-sprint-protocol`。
- `release` 用于标识事项服务的版本目标；`sprint` 用于标识事项所在执行轮次或协作索引，不替代 GitHub 状态语义。
- 治理基线自举允许 `Issue + decision + exec-plan` 作为 bootstrap contract。
- 非治理基线事项进入实现前必须有 formal spec 输入；formal spec 绑定到上位 FR，而不是绑定到 Phase 或 Work Item。
- 每个执行回合必须有且仅有一个 active `exec-plan` 与当前 `item_key` 一一对应；上位前提事项可在该工件中被引用，但不替代当前事项的 active 工件。

## checkpoint / resume / compact 规则

- 长任务统一按 `kickoff -> checkpoint -> compact -> resume -> handoff -> merge-ready` 执行。
- `核心事项` 强制存在 `exec-plan`，并记录事项上下文、停点、下一步、已验证项、未决风险、最近一次 checkpoint 对应的 head SHA。
- `exec-plan` 中的 head SHA 用于恢复最近一次 checkpoint，不替代 guardian 对当前受审 head SHA 的绑定与 merge gate 校验。
- 仅当执行回合显式推进新的 checkpoint 时，才刷新 `exec-plan` 中记录的 checkpoint head。
- review 结论、GitHub checks、PR 关联、索引入口等审查态信息的更新，不自动构成新的 checkpoint。
- checkpoint 与 resume 必须保持 `Issue`、`item_key`、`release`、`sprint` 一致；若事项上下文发生变化，必须先更新 active `exec-plan`，再继续执行。
- checkpoint 必须说明当前改动推进了哪个 `release` 目标，以及该事项在当前 `sprint` 中的角色或位置。
- `compact` 仅压缩已入库且可复验的信息，不得压缩未落盘前提。
- `compact` 不得压缩未落盘的事项上下文判断，包括 `release`、`sprint` 绑定与事项角色判定。
- 具体协议以 `docs/process/agent-loop.md` 为准。

## review / guardian / CI 职责边界

- reviewer 负责基于 [spec_review.md](./spec_review.md) 或 [code_review.md](./code_review.md) 的 rubric 做实质审查，判断边界、语义正确性、风险、验证充分性与是否存在阻断项。
- reviewer 的结论不由工件完整性检查、CI 结果或 guardian 结果自动推导。
- review rubric 不等于 merge gate；rubric 回答“是否值得进入下一阶段 / 是否达到 merge-ready 质量”，merge gate 回答“当前 head 是否允许受控合并”。
- guardian 负责对当前 PR head 执行合并前审查门禁，输出绑定 `head SHA` 的 `verdict` 与 `safe_to_merge`，不替代 reviewer 的实质判断，也不替代 CI 的自动化校验。
- CI 负责自动化检查与回归验证，回答“自动化门禁是否通过”，不替代 reviewer 的语义审查，也不替代 guardian 的 merge gate 结论。
- `merge_pr` 负责消费当前 head 对应的 guardian 结果并执行受控合并，不生产 reviewer rubric，也不替代 guardian / CI 作出前置判断。
- merge gate 由 guardian verdict、`safe_to_merge`、GitHub checks、PR 状态与 head 一致性共同构成；它不是 reviewer rubric 的别名。

## review 输入最小化原则

- review 与 guardian 的输入应优先采用与当前事项、当前 head、当前风险直接相关的最小必要上下文。
- 优先提供：`Issue`、active `exec-plan`、相关 formal spec / bootstrap contract、PR 描述、风险/验证证据、与当前 diff 直接相关的流程或规约文档。
- 不应把与当前判断无关的历史讨论、相邻事项材料或整仓重复探索默认塞给 reviewer / guardian。
- 若要补充额外上下文，必须以“消除当前阻断或验证当前 head 风险”为目的，而不是让审查器无限制二次侦察。

## integration project 联动规则

- canonical integration contract 的单一真相源固定为 [`scripts/policy/integration_contract.json`](./scripts/policy/integration_contract.json) 与 [`scripts/integration_contract.py`](./scripts/integration_contract.py)。
- issue / work item 消费 issue scope 字段；PR / guardian / merge gate 消费 PR scope 字段。字段集合、枚举值、组合约束、`integration_ref` 归一规则与 legacy 兼容策略都只以 canonical contract 为准。
- 默认执行真相源仍是当前仓库的 GitHub Project；仅当事项触及跨仓共享契约、跨仓依赖或联合验收时，才查看 owner 级 integration project。
- 满足以下任一条件时，执行者必须在开工前查看 `integration_ref` 对应的 integration issue / item，并按 canonical contract 进入 `integration_check_required` 路径：
  - 改共享输入输出
  - 改错误码或错误语义
  - 改 `raw` / `normalized` / `diagnostics` / `observability`
  - 改 `task_id` / `request_id` / `run_id`
  - 改执行模式或 gate 口径
  - 依赖另一仓库先做、同步做或共同验收
  - 影响联合 PoC、联合回归或共享桥接能力
- `open_pr` 负责基于 canonical contract 校验上位 issue / work item 元数据并生成 PR `integration_check`；`pr_guardian` 与 `merge_pr` 只消费同一 contract 结果，不再各自定义一套 integration 规则。
- integration project 只承载跨仓协调真相；本地 issue / PR / review 仍是实现、关闭语义与 merge gate 的真相源。
- 存量 PR 兼容仍走受控 legacy 路径：
  - issue lookup failure 继续 fail-closed
  - issue 存在但尚未声明 canonical integration 字段时，guardian 可沿用 legacy 路径
  - 一旦上位 issue / work item 已声明 canonical integration 字段，PR `integration_check` 就必须完整存在并与之完全一致

## stop conditions

- 缺少必需输入（Issue、事项上下文、formal spec 或 bootstrap contract）。
- 任一进入执行回合的事项缺少 `item_key` / `item_type` / `release` / `sprint` 绑定。
- 当前改动越过阶段边界或破坏规约/实现分离。
- 关键门禁失败且无法在当前回合消除。
- guardian 结果不是 `APPROVE` 或 `safe_to_merge=false`。

## 何时必须更新 `exec-plan`

- 完成一组可验证改动后必须更新一次 checkpoint。
- 变更停点、风险、验证结论或形成新的 checkpoint 时必须更新。
- 若仅发生后续跟进 commit、但尚未形成新的 checkpoint，可保留最近一次 checkpoint head，并由 guardian state 绑定当前受审 head。
- 若仅补充 review / merge gate 元数据，而未显式推进新的执行停点，不要求刷新 checkpoint head。
- 变更 `item_key`、`item_type`、`release`、`sprint` 或事项在当前轮次中的定位时必须更新。
- 进入 review、进入 merge gate 前必须更新到最新状态。

## 何时允许进入 `open_pr` / `merge_pr`

- 进入 `open_pr` 条件：
  - 已声明 PR class 且与改动类别一致
  - 已通过受控入口显式填写完整事项上下文，且该事项在进入当前执行回合前已完成补齐
  - 当前事项存在与 `item_key` 唯一匹配的 active `exec-plan`；历史事项可继续使用保留文件名，但不得出现多个 active 工件
  - active `exec-plan` 的 `item_key` / `Issue` / `item_type` / `release` / `sprint` 与受控入口填写值一致
  - 若 active `exec-plan` 声明 `active 收口事项`，其值必须与当前 `item_key` 一致
  - PR 描述、风险与验证信息可映射回 `Issue`、`item_key`、`release`、`sprint`
  - `核心事项` 已满足 formal spec 或 bootstrap contract 输入
  - 风险、验证、回滚信息已就绪
- 进入 `merge_pr` 条件：
  - reviewer 已按适用 rubric 完成当前事项所需的实质审查
  - 以下 merge gate 条件必须同时满足：
  - latest guardian verdict=`APPROVE`
  - `safe_to_merge=true`
  - GitHub checks 全绿
  - PR 非 Draft，且审查与合并使用同一 head SHA
  - 若上位 issue / work item 已声明 canonical integration 字段，则 guardian 必须通过 canonical contract 确认 PR 的 `integration_check` 与其保持一致
  - 若 `merge_gate=integration_check_required`，则 merge gate 必须记录提 PR 前检查已完成，并在合并前再次核对 `integration_ref` 对应 integration issue / item 的状态、依赖与联合验收约束
