# GOV-0035-top-level-positioning-alignment 执行计划

## 关联信息

- item_key：`GOV-0035-top-level-positioning-alignment`
- Issue：`#205`
- item_type：`GOV`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`无`
- 关联 decision：`docs/decisions/ADR-GOV-0035-top-level-positioning-alignment.md`
- 关联 PR：`待补充`
- 状态：`active`
- active 收口事项：`GOV-0035-top-level-positioning-alignment`

## 目标

- 修订 `AGENTS.md`、`vision.md` 与 `docs/roadmap-v0-to-v1.md` 的顶层定位叙事，使 Syvert 不再被定义为“采集底座”，而被定义为“统一承载和治理互联网操作任务及其资源的稳定底座”。
- 在不改写 formal spec 与历史验证事实的前提下，明确 `v0.x` 的 `content_detail_by_url` / 双参考适配器路径只是当前验证切片，不是长期能力边界。

## 范围

- 本次纳入：
  - `AGENTS.md`
  - `vision.md`
  - `docs/roadmap-v0-to-v1.md`
  - `docs/decisions/ADR-GOV-0035-top-level-positioning-alignment.md`
  - `docs/exec-plans/GOV-0035-top-level-positioning-alignment.md`
- 本次不纳入：
  - `docs/specs/**`
  - `docs/releases/**`
  - `docs/sprints/**`
  - `docs/research/**`
  - runtime / adapter / tests 实现
  - formal spec / contract 命名与字段重构

## 当前停点

- 已完成定位讨论，结论收敛为：`Syvert 是一个统一承载和治理互联网操作任务及其资源的稳定底座。`
- 已完成影响分析：本轮最小修订集固定为 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md`；formal spec 与历史工件暂不回写。
- `#205` 已建立为当前治理 Work Item，bootstrap decision 与 active exec-plan 已落盘，三份顶层文档的首轮定位修订已经完成且本地门禁通过；当前停点是整理差异、提交并创建 governance PR。

## 下一步动作

- 提交当前定位修订与治理 bootstrap 工件。
- 推送分支，并通过受控入口创建单独的 governance PR。
- 在 PR 建立后同步 `关联 PR`、review 停点与当前受审 head 的 metadata。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.5.0` 资源能力抽象收敛阶段补齐顶层定位真相，避免后续 formal spec 与实现继续被“采集底座”旧叙事牵引。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：顶层定位治理收口 Work Item。
- 阻塞：
  - 若顶层定位不先收敛，后续关于 `CollectionPolicy`、`raw + normalized` 与操作语义的 formal spec 讨论会持续混入“长期定位”和“当前切片”两层语义。

## 已验证项

- 已核对 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md` 的现有定位与边界表述。
- 已核对 `WORKFLOW.md` 与 `docs/AGENTS.md` 的 Work Item / worktree / open_pr 约束。
- `gh issue edit 205 --title '治理工作项：修订 Syvert 顶层定位文档' --body-file /tmp/gov-0035-issue.md --add-label governance`
  - 结果：已建立并收敛当前治理 Work Item `#205`
- `python3 scripts/create_worktree.py --issue 205 --class governance`
  - 结果：已创建并绑定独立 worktree `/Users/mc/code/worktrees/syvert/issue-205-syvert`，执行分支 `issue-205-syvert`
- 已完成 `AGENTS.md`、`vision.md` 与 `docs/roadmap-v0-to-v1.md` 的首轮定位修订。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `BASE=$(git merge-base origin/main HEAD); HEAD_SHA=$(git rev-parse HEAD); python3 scripts/governance_gate.py --mode ci --base-sha "$BASE" --head-sha "$HEAD_SHA" --head-ref issue-205-syvert`
  - 结果：通过

## 未决风险

- 若 `vision.md` 只替换一句 slogan、不同步改写价值叙事与阶段边界，仓库仍会同时保留两套互相冲突的定位。
- 若 `docs/roadmap-v0-to-v1.md` 不明确“验证切片 != 长期边界”，后续仍会把 `content_detail_by_url` 误读为 Syvert 的长期对象模型。
- 若本次顺手改写 `docs/specs/**`，会把定位修订和 formal spec 语义改写混成同一 PR，破坏当前最小范围。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本次对三份顶层文档、bootstrap decision 与当前 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `d7dc70934b15b2f4812795a9c16b71b4de41f367`
