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
- 当前仍处于 pre-PR 阶段；formal spec 门禁已通过，但受控入口尚未消费当前未提交变更。

## 下一步动作

- 将 formal spec 核心文件与 active exec-plan 纳入当前执行回合的 git 索引。
- 通过 `open_pr.py --class spec --issue 141 ... --dry-run` 验证受控入口。
- 在 dry-run 通过后提交、推送并创建 `#141` 的 spec PR。

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

## 未决风险

- 若 formal spec 不把 query 错误 contract 写死，`#142` 将被迫替 requirement 做决策。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销 `docs/specs/FR-0009-cli-task-query-and-core-path/` 与相关索引工件的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `8175221a9ca4dd2adc2c62d7a05ce46b4fabf411`
