# CHORE-0126-fr-0009-formal-spec-closeout 执行计划

## 关联信息

- item_key：`CHORE-0126-fr-0009-formal-spec-closeout`
- Issue：`#141`
- item_type：`CHORE`
- release：`v0.3.0`
- sprint：`2026-S16`
- 关联 spec：`docs/specs/FR-0009-cli-task-query-and-core-path/`
- 状态：`active`
- active 收口事项：`CHORE-0126-fr-0009-formal-spec-closeout`

## 目标

- 建立并收口 `FR-0009` formal spec 套件，冻结 CLI `run/query` public surface、legacy 平铺执行入口兼容边界、query 成功/失败输出 contract 与 same-path 边界。

## 范围

- 本次纳入：
  - `docs/specs/FR-0009-cli-task-query-and-core-path/`
  - `docs/exec-plans/FR-0009-cli-task-query-and-core-path.md`
  - `docs/exec-plans/CHORE-0126-fr-0009-formal-spec-closeout.md`
  - `docs/releases/v0.3.0.md`
  - `docs/sprints/2026-S16.md`
- 本次不纳入：
  - `syvert/**`、`tests/**` 运行时代码与测试
  - `FR-0008` 的 durable `TaskRecord` contract 改写
  - `#143/#144` 的 closeout 语义

## 当前停点

- `issue-141-fr-0009-formal-spec` 已作为 `#141` 的独立 spec worktree 建立。
- `FR-0009` formal spec 套件、requirement container 与最小 release / sprint 索引已经在当前分支首次落盘。
- `#141` 当前为 `OPEN`，GitHub body 中的 `sprint` 已同步为 `2026-S16`。
- 受控入口 `open_pr.py --class spec --issue 141 ... --dry-run` 已通过，spec PR `#154` 已创建并指向当前事项。
- guardian 对旧 head 的审查先后指出了四类阻断：formal spec 回退了上游共享请求 contract / 泄漏实现细节，`invalid_cli_arguments` 在可恢复 `--task-id` 时仍可能丢失用户查询键，`plan.md` 中存在与串行收口策略不一致的并行描述，以及 `#141` 允许写集未把 requirement container 纳入合法范围。
- 当前分支已把 `FR-0009` spec 收敛回 `FR-0004` / `FR-0008` 已冻结的共享请求模型与 durable-truth contract，补齐“可恢复 query key 时必须回显用户 `task_id`”的参数错误 contract，把 legacy URL 兼容投影与 `#141 -> #142 -> #143 -> #144` 串行关系写死，并把 requirement container 明确纳入 `#141` 合法 docs scope；当前停点是等待绑定最新 head 的 guardian 复核。

## 下一步动作

- 提交并推送本次 formal spec 语义修正，让 PR `#154` 的最新 head 与 active exec-plan 保持一致。
- 等待 guardian 产出绑定当前 PR head 的 verdict 与 `safe_to_merge` 结论。
- 在 guardian / merge gate 全部通过后，使用 `python3 scripts/merge_pr.py 154 --delete-branch` 执行受控 squash merge。
- `#141` 合入主干后，把 `#128` 的 formal spec 字段从 `planned` 收敛到已入库真相，再切换到 `#142`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.3.0` 把 CLI 查询与同路径执行闭环从 GitHub 意图推进到 implementation-ready 的 formal contract。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0009` formal spec closeout Work Item。
- 阻塞：
  - formal spec 未冻结前，`#142/#143` 不应自行扩张 requirement。

## 已验证项

- 已核对 `FR-0008` 已冻结 durable `TaskRecord`、fail-closed 回读与 no-shadow-schema 边界。
- 已核对 `docs/roadmap-v0-to-v1.md` 把 `v0.3.0` 定义为 CLI 查询与同路径执行闭环。
- `gh issue view 141 --json body,projectItems,state,title,url`
  - 结果：`#141` 仍为 `OPEN`，Project 状态为 `Todo`，GitHub body 中的 `sprint` 已为 `2026-S16`
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD) --head-ref issue-141-fr-0009-formal-spec`
  - 结果：通过
- `python3 scripts/open_pr.py --class spec --issue 141 --item-key CHORE-0126-fr-0009-formal-spec-closeout --item-type CHORE --release v0.3.0 --sprint 2026-S16 --title "spec: 收口 FR-0009 的 formal spec" --dry-run`
  - 结果：通过
- `gh pr checks 154`
  - 结果：Commit / Docs / Governance / Spec Guard checks 全绿
- guardian 旧 head 审查摘要
  - 结果：指出 shared request contract drift、实现细节泄漏到 formal spec、`invalid_cli_arguments` 可能丢失可恢复的查询键、`plan.md` 存在并行描述，以及 `#141` 合法写集定义遗漏 requirement container；当前分支已据此修正，待最新 head 复核

## 未决风险

- 若 formal spec 不把 query 错误 contract 写死，`#142` 将被迫替 requirement 做决策。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `docs/specs/FR-0009-cli-task-query-and-core-path/` 与相关索引工件的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `2dd45df4fe0d8ca18cc342f2f4d7116d15955792`
