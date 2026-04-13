# CHORE-0099-fr-0005-parent-closeout 执行计划

## 关联信息

- item_key：`CHORE-0099-fr-0005-parent-closeout`
- Issue：`#99`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- 关联 decision：
- 关联 PR：`#100`
- 状态：`active`
- active 收口事项：`CHORE-0099-fr-0005-parent-closeout`

## 目标

- 在不引入新实现、新 formal spec 语义或额外 implementation Work Item 的前提下，通过合法 Work Item `#99` 完成父 FR `#65` 的最终 closeout。
- 把 `FR-0005` 的 formal spec、`#69/#70` 实现、release / sprint 索引与 GitHub issue 真相映射回同一条父事项证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/FR-0005-standardized-error-model-and-adapter-registry.md`
  - `docs/exec-plans/CHORE-0099-fr-0005-parent-closeout.md`
  - `docs/exec-plans/CHORE-0069-fr-0005-standardized-error-model.md`
  - `docs/exec-plans/CHORE-0070-fr-0005-adapter-registry.md`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - GitHub `#65` issue 正文修正
  - GitHub `#65` closeout 评论
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0005` formal spec 语义改写
  - `FR-0006`、`FR-0007` 或其它 FR 的事项状态调整

## 当前停点

- `origin/main@eb400dcfddecb05ddeb3fd67b30ad223c6b3d063` 已包含 `FR-0005` closeout 所需的关键前提：PR `#78`、`#97`、`#98`。
- `#77` 已由 PR `#78` 合入并关闭；`#69` 已由 PR `#97` 合入并关闭；`#70` 已由 PR `#98` 合入并关闭。
- 当前 `FR-0005` GitHub closeout 仍包含 Work Item `#99` 与父 FR `#65`；`#81` 为 `spec_issue_sync.py` 自动镜像，已关闭且不得重新打开。
- `gh issue list --repo MC-and-his-Agents/Syvert --state open --search 'FR-0005'` 当前仅返回 `#65` 与 `#99`，确认不存在其他 open 的 `FR-0005` implementation 子事项或 open 镜像。
- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-99-chore-fr-0005`。

## 下一步动作

- 把 `FR-0005` requirement container、`#69/#70` 历史实现记录、release / sprint 索引与 `#99` 对齐到“唯一 active closeout 入口”后的主干真相。
- 当前 head 已完成门禁与受控 PR 创建，下一步进入 guardian / merge gate。
- 合并后先关闭当前 Work Item `#99`，再修正 GitHub `#65` 正文、发布 `#65` closeout 评论并关闭 `#65`。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 完成 `FR-0005` 父事项收口，使错误模型与 adapter registry 的 requirement 已被 formal spec、主干实现、验证证据与 GitHub 关闭语义完整消费。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0005` 父事项 closeout Work Item。
- 阻塞：
  - 必须先保证 `#77/#69/#70` 全部关闭，且 release / sprint / exec-plan 不再把 `#69/#70` 误表述为当前 active 实现入口。
  - 必须在关闭前修正 `#65` 正文，使其反映 formal spec、错误模型实现、registry 实现与当前 parent closeout 入口的主干真相。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- `gh issue view 65 --repo MC-and-his-Agents/Syvert`
  - 结果：`#65` 为 `OPEN`，且当前仍是 `FR-0005` 的 canonical requirement 容器
- `gh issue view 69 --repo MC-and-his-Agents/Syvert`
  - 结果：`#69` 为 `CLOSED`
- `gh issue view 70 --repo MC-and-his-Agents/Syvert`
  - 结果：`#70` 为 `CLOSED`
- `gh issue view 77 --repo MC-and-his-Agents/Syvert`
  - 结果：`#77` 为 `CLOSED`
- `gh issue view 81 --repo MC-and-his-Agents/Syvert`
  - 结果：`#81` 为 `CLOSED`，且为 `spec_issue_sync.py` 自动镜像
- `gh issue view 99 --repo MC-and-his-Agents/Syvert`
  - 结果：`#99` 已建立为当前父事项 closeout Work Item
- `gh pr view 78 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 97 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`
- `gh pr view 98 --repo MC-and-his-Agents/Syvert --json state,mergedAt,mergeCommit`
  - 结果：`state=MERGED`，`mergeCommit=eb400dcfddecb05ddeb3fd67b30ad223c6b3d063`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/commit_check.py --mode pr --base-ref origin/main --head-ref HEAD`
  - 结果：已校验 1 条提交信息，全部通过
- `python3 scripts/open_pr.py --class docs --issue 99 --item-key CHORE-0099-fr-0005-parent-closeout --item-type CHORE --release v0.2.0 --sprint 2026-S15 --title 'docs(closeout): 收口 FR-0005 父事项' --closing fixes --dry-run`
  - 结果：通过
- 已创建当前受审 PR：`#100 https://github.com/MC-and-his-Agents/Syvert/pull/100`

## closeout 证据

- formal spec 证据：PR `#78` 已把错误模型与 adapter registry formal spec 合入主干，对应 `docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- implementation 证据：
  - PR `#97` / `#69`：统一 `invalid_input`、`unsupported`、`runtime_contract`、`platform` 四类失败语义
  - PR `#98` / `#70`：落地 adapter registry materialization、lookup、capability discovery 与 fail-closed
- release / sprint 证据：`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 将在本回合回链 `#65/#77/#69/#70/#99` 与 PR `#78/#97/#98`
- GitHub closeout 证据：当前剩余 GitHub closeout issue 为 active Work Item `#99` 与父 FR `#65`；本回合合入后应先关闭 `#99`，再关闭 `#65`

## GitHub closeout 工件

- `#65` 正文修正目标：
  - 明确 formal spec 已由 PR `#78` 合入主干
  - 明确错误模型实现已由 `#69` / PR `#97` 落地
  - 明确 adapter registry 实现已由 `#70` / PR `#98` 落地
  - 将父事项 closeout 入口补为 `#99`
  - 子 Work Item 保持：`#69`、`#70`、`#99`
- `#65` closeout 评论草案：
  - `FR-0005` formal spec 已由 PR `#78` 合入主干，spec 真相位于 `docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
  - `#69` / PR `#97` 已完成标准化错误模型实现，统一 `invalid_input`、`unsupported`、`runtime_contract`、`platform` 四类失败语义
  - `#70` / PR `#98` 已完成 adapter registry materialization、lookup、capability discovery 与 fail-closed 实现
  - 当前父事项 closeout 已由 `#99` 承接，`docs/releases/v0.2.0.md`、`docs/sprints/2026-S15.md` 与 active exec-plan 已与 GitHub 真相一致
  - 当前不存在遗漏的 `FR-0005` implementation 子事项，且 `#81` 保持关闭
- `#65` 正文草案：

```md
## 目标

为 `v0.2.0` 建立标准化错误模型与 adapter registry 契约，确保能力发现与错误分类保持一致。

## 明确不在范围内

- 输入目标与采集策略建模
- adapter contract test harness 与假适配器细节
- 版本 gate 与双参考适配器回归

## 关闭条件

- formal spec 已由 PR `#78` 建立并通过审查
- 标准化错误模型已由 `#69` / PR `#97` 落地，并与 formal spec 对齐
- adapter registry 已由 `#70` / PR `#98` 落地，并与 formal spec 对齐
- 父事项 closeout 已由 `#99` 承接并完成 release / sprint / exec-plan / GitHub 语义收口

## 关系

- 层级：`FR`
- 版本：`v0.2.0`
- 父阶段：`#63`
- formal spec：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- 子 Work Item：`#69`, `#70`, `#99`
```

## 未决风险

- 若 `#65` 关闭前仍把 `#69/#70` 或 release / sprint 索引标记为 active，会留下双 active 执行语义。
- 若 `#65` 关闭前不修正 GitHub 正文与 closeout 评论，后续回溯 `FR-0005` 的 formal spec / implementation / closeout 证据仍需手工拼接。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 `docs/exec-plans/FR-0005-standardized-error-model-and-adapter-registry.md`、`docs/exec-plans/CHORE-0099-fr-0005-parent-closeout.md`、`docs/exec-plans/CHORE-0069-fr-0005-standardized-error-model.md`、`docs/exec-plans/CHORE-0070-fr-0005-adapter-registry.md`、`docs/releases/v0.2.0.md` 与 `docs/sprints/2026-S15.md` 的增量修改。
- GitHub 侧回滚：
  - 若已编辑 `#65` 正文但 PR 未合入，恢复 `#65` 到 closeout 前正文，并保留 `#65/#99` 为 `OPEN`
  - 若已发布 `#65` closeout 评论但发现仓内工件仍不一致，在 `#65` 追加纠正评论并停止关闭动作
  - 若 `#65` 已关闭后发现 closeout 事实错误，先重新打开 `#65`，再通过独立 revert PR 与新的 closeout 回合修复仓内 / GitHub 状态

## 最近一次 checkpoint 对应的 head SHA

- `eb400dcfddecb05ddeb3fd67b30ad223c6b3d063`
