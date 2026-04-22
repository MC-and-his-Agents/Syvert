# HOTFIX-0145-revert-fr-0015-evidence-closeout 执行计划

## 关联信息

- item_key：`HOTFIX-0145-revert-fr-0015-evidence-closeout`
- Issue：`#209`
- item_type：`HOTFIX`
- release：`v0.5.0`
- sprint：`2026-S18`
- 关联 spec：`docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
- 关联 PR：`#210`
- 状态：`active`
- active 收口事项：`HOTFIX-0145-revert-fr-0015-evidence-closeout`

## 目标

- 通过独立 revert PR 回退 `PR #204`（merge commit `a8b6ffc87b41afae5d4d9c4e95de74791e521b5b`）带入 `main` 的 `FR-0015` implementation closeout 增量。
- 恢复 `latest guardian verdict=APPROVE`、`safe_to_merge=true`、checks 全绿、review/merge 同一 head 这一 merge gate 真相，不让 `main` 继续承载一次越过门禁的实现 closeout。
- 为后续在新 Work Item 下重新推进 `#197` 留出干净主干，而不是在已越界合入的基础上继续补丁。

## 范围

- 本次纳入：
  - 回退 `#204` 带入的 machine-readable evidence registry module
  - 回退 `#204` 带入的 FR-0015 runtime traceability tests
  - 回退 `#204` 带入的 evidence baseline artifact
  - 回退 `#204` 带入的 implementation closeout exec-plan
  - 修正 `docs/exec-plans/FR-0015-dual-reference-resource-capability-evidence.md` 的追溯口径
  - 新增当前 hotfix 回合的 active exec-plan
- 本次不纳入：
  - 重新实现 `#197`
  - 修改 `docs/specs/FR-0015-dual-reference-resource-capability-evidence/`
  - 修改 `#195/#196` 的实现或 formal spec
  - release / sprint 索引扩写

## 当前停点

- `PR #204` 已于 `2026-04-22` 合入 `main`，merge commit 为 `a8b6ffc87b41afae5d4d9c4e95de74791e521b5b`。
- 该次合入发生时，latest guardian 并未对当前受审 head 给出明确 `APPROVE`；虽然 checks 全绿，但 merge gate 真相未闭合。
- 当前 hotfix worktree 已从 `main@a8b6ffc87b41afae5d4d9c4e95de74791e521b5b` 建立：`/Users/mc/code/worktrees/syvert/issue-209-pr-204-latest-guardian-approve`。
- 当前分支已生成 revert checkpoint `0f55583c20200ce071ddb58d203243cc35e4af92`，完成对 `#204` 主体实现增量的逆向撤销；当前停点是补齐 revert 回合所需的最小治理追溯工件并进入验证。
- 当前受审 revert PR 已创建为 `#210`，后续 guardian / checks / merge gate 反馈统一回写到本 exec-plan。

## 下一步动作

- 完成 `FR-0015` requirement container 的 revert-trace 修正，使其不再把 `#204` 作为当前有效 implementation closeout 真相。
- 运行当前 revert PR 所需的本地门禁与最小回归。
- 通过 `open_pr` 创建受控 revert PR，随后等待 latest guardian `APPROVE` 与 checks 全绿，再执行 squash merge。

## 当前 checkpoint 推进的 release 目标

- 撤销一次未满足 latest guardian APPROVE merge gate 的 `v0.5.0` implementation closeout 合入，恢复主干对 `FR-0015` 的可信发布前提。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0015` implementation closeout 的 hotfix revert Work Item。
- 阻塞：
  - 在本事项合入前，`main` 上的 `FR-0015` implementation truth 与 merge gate 真相不一致。
  - 在本事项合入前，不应继续把 `#204` 带入的 machine-readable evidence registry 当作可继续演进的主干基线。

## 已验证项

- `gh issue create`
  - 结果：已创建当前 Work Item `#209 https://github.com/MC-and-his-Agents/Syvert/issues/209`
- `python3 scripts/create_worktree.py --issue 209 --class implementation --base main`
  - 结果：已创建当前 worktree `issue-209-pr-204-latest-guardian-approve`，base SHA=`a8b6ffc87b41afae5d4d9c4e95de74791e521b5b`
- `git revert --no-edit a8b6ffc87b41afae5d4d9c4e95de74791e521b5b`
  - 结果：已生成 revert 变更，并重提为中文 Conventional Commit
- `git commit -m 'revert(runtime): 回退 FR-0015 双参考资源能力证据基线'`
  - 结果：已生成当前 revert checkpoint `0f55583c20200ce071ddb58d203243cc35e4af92`
- `python3 scripts/open_pr.py --class implementation --issue 209 --item-key HOTFIX-0145-revert-fr-0015-evidence-closeout --item-type HOTFIX --release v0.5.0 --sprint 2026-S18 --title 'revert(runtime): 回退 FR-0015 双参考资源能力证据基线' --base main --closing fixes`
  - 结果：已创建当前受审 revert PR `#210 https://github.com/MC-and-his-Agents/Syvert/pull/210`

## 未决风险

- 若只回退代码文件而不修正 requirement / exec-plan 追溯口径，仓内仍会保留“`#204` 是当前有效 implementation closeout”的错误真相。
- 若在 revert PR 上再次跳过 latest guardian `APPROVE`，会重复同一类流程违背。
- 若后续重新推进 `#197` 时复用旧分支/旧 PR，而不是新 Work Item / 新 PR，GitHub 调度层会再次混淆关闭语义。

## 回滚方式

- 如需恢复 `#204` 的内容，必须在新的受控 Work Item 下重新提交 implementation PR，并满足 latest guardian `APPROVE` merge gate；不得直接反向回滚当前 hotfix。

## 最近一次 checkpoint 对应的 head SHA

- `0f55583c20200ce071ddb58d203243cc35e4af92`
