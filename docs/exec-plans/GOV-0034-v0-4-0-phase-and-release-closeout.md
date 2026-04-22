# GOV-0034-v0.4.0-phase-and-release-closeout 执行计划

## 关联信息

- item_key：`GOV-0034-v0-4-0-phase-and-release-closeout`
- Issue：`#185`
- item_type：`GOV`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：无（发布/治理收口事项）
- 关联 decision：`docs/decisions/ADR-GOV-0034-v0-4-0-phase-and-release-closeout.md`
- 关联 PR：`#186`、`#187`
- 状态：`active`
- active 收口事项：`GOV-0034-v0-4-0-phase-and-release-closeout`

## 目标

- 在不引入新 runtime、formal spec 或测试语义的前提下，通过合法 Work Item `#185` 完成 `v0.4.0` 的 phase / release 发布收口。
- 把 `docs/releases/v0.4.0.md`、`docs/sprints/2026-S17.md`、Git tag、GitHub Release 与 GitHub issue 真相收口到同一条版本 closeout 证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/GOV-0034-v0-4-0-phase-and-release-closeout.md`
  - `docs/decisions/ADR-GOV-0034-v0-4-0-phase-and-release-closeout.md`
  - `docs/releases/v0.4.0.md`
  - `docs/sprints/2026-S17.md`
  - GitHub `#162` / `#185` issue 正文、关闭语义与最终评论对齐
  - git tag `v0.4.0`
  - GitHub Release `v0.4.0`
- 本次不纳入：
  - 任何新的 runtime / adapter / test 实现
  - `FR-0010` / `FR-0011` / `FR-0012` formal spec 语义改写
  - `v0.5.0` 资源能力抽象或跨版本治理重构

## 当前停点

- `origin/main@c9ce7362215c2748df6d7f3c541ae613a62fdeea` 已包含 `v0.4.0` 所需的全部 formal spec、runtime、reference adapter 收口、发布 carrier 与回归修复：PR `#169/#170/#171/#176/#178/#180/#182/#184/#186`。
- `#162` 已关闭，`#163/#165/#167` 及其下属 Work Item 也已关闭，`v0.4.0` 的功能与 FR closeout 目标已经完成。
- `v0.4.0` tag 已创建并推送，GitHub Release `v0.4.0` 已发布。
- `#185` 已建立为承接 `v0.4.0` phase / release closeout 的合法治理 Work Item。
- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-185-v0-4-0`，当前分支为 `issue-185-v0-4-0-phase-b`。
- 当前回合已进入 `metadata-only closeout follow-up`：当前分支只负责把 `docs/releases/v0.4.0.md`、`docs/sprints/2026-S17.md` 与本 exec-plan 从阶段 A 发布前真相同步到正式发布完成真相。
- 阶段 B metadata-only/docs PR `#187` 已创建，当前回合正等待 guardian / merge gate。
- 本事项按同一 Work Item 的两阶段模型推进：阶段 A 已完成仓内 carrier 合入；阶段 B 正在回写最终发布真相并收口 GitHub closeout。

## 下一步动作

- 在当前分支把 release / sprint 索引与本 exec-plan 同步到正式发布完成真相。
- 通过受控 docs PR 合入阶段 B metadata-only closeout follow-up。
- 合并阶段 B 后回写并关闭 `#185`，并补 `#162` 的最终 closeout 评论。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 完成“从功能收口到正式发布”的最后一段链路，使 release/sprint 索引、发布锚点与 GitHub closeout 进入一致完成态。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.4.0` 的 phase / release 发布 closeout Work Item。
- 阻塞：
  - 阶段 B 需要把阶段 A 发布前基线与最终 published truth 严格区分，不能把 `#186/c9ce736...` 误写成已经承载最终仓内发布真相。
  - active `exec-plan` 的历史负证据必须按阶段标注，不能和当前阶段 B 的已发布事实混写成同一组当前验证结果。

## 已验证项

### 阶段 A 基线验证

- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 162 --json state`
  - 结果：`#162` 为 `CLOSED`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 163 --json state`
  - 结果：`#163` 为 `CLOSED`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 165 --json state`
  - 结果：`#165` 为 `CLOSED`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 167 --json state`
  - 结果：`#167` 为 `CLOSED`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh release view v0.4.0`
  - 结果：`release not found`
- `git tag --list 'v0.4.0'`
  - 结果：未找到 `v0.4.0`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD) --head-ref issue-185-v0-4-0`
  - 结果：通过
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/open_pr.py --class docs --issue 185 --item-key GOV-0034-v0-4-0-phase-and-release-closeout --item-type GOV --release v0.4.0 --sprint 2026-S17 --title 'docs(release): 建立 v0.4.0 发布收口 carrier' --closing fixes --dry-run`
  - 结果：通过
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/open_pr.py --class docs --issue 185 --item-key GOV-0034-v0-4-0-phase-and-release-closeout --item-type GOV --release v0.4.0 --sprint 2026-S17 --title 'docs(release): 建立 v0.4.0 发布收口 carrier' --closing fixes`
  - 结果：已创建 PR `#186`
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 186 --post-review`
  - 结果：首轮 `REQUEST_CHANGES`
  - 已识别阻断：
    - active `exec-plan` 不得把可变的 live review head 写成当前真相；当前分支已移除该绑定，改回只保留 checkpoint truth 与 review 状态描述
  - 结果：第二轮 `REQUEST_CHANGES`
  - 已识别阻断：
    - `docs/releases/v0.4.0.md` 与 `docs/sprints/2026-S17.md` 不得把阶段 A 发布前真相误写成“发布完成真相”；当前分支已统一改为阶段 A 发布前表述
  - 结果：第三轮 `APPROVE`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh pr view 186 --json state,mergeCommit`
  - 结果：PR `#186` 已 `MERGED`，merge commit 为 `c9ce7362215c2748df6d7f3c541ae613a62fdeea`

### 阶段 B 当前验证

- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue reopen 185`
  - 结果：已重新打开 `#185`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 185 --json state`
  - 结果：`#185` 为 `OPEN`
- `git tag -a v0.4.0 -m 'v0.4.0'`
  - 结果：已在主干提交 `c9ce7362215c2748df6d7f3c541ae613a62fdeea` 上创建 annotated tag `v0.4.0`
- `git push origin v0.4.0`
  - 结果：已推送 tag `v0.4.0`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh release create v0.4.0 --title 'v0.4.0' --notes-file /tmp/v0.4.0-release.md`
  - 结果：已创建 GitHub Release `v0.4.0`
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过
- `python3 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD`
  - 结果：通过
- `python3 scripts/governance_gate.py --mode ci --base-sha $(git merge-base origin/main HEAD) --head-sha $(git rev-parse HEAD) --head-ref issue-185-v0-4-0`
  - 结果：通过
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/open_pr.py --class docs --issue 185 --item-key GOV-0034-v0-4-0-phase-and-release-closeout --item-type GOV --release v0.4.0 --sprint 2026-S17 --title 'docs(release): 同步 v0.4.0 发布完成真相' --closing fixes --dry-run`
  - 结果：通过
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/open_pr.py --class docs --issue 185 --item-key GOV-0034-v0-4-0-phase-and-release-closeout --item-type GOV --release v0.4.0 --sprint 2026-S17 --title 'docs(release): 同步 v0.4.0 发布完成真相' --closing fixes`
  - 结果：已创建 PR `#187`
- `env -u GH_TOKEN -u GITHUB_TOKEN python3 scripts/pr_guardian.py review 187 --post-review`
  - 结果：首轮 `REQUEST_CHANGES`
  - 已识别阻断：
    - `#186/c9ce736...` 只能表述为阶段 A 发布 carrier 基线，不能误写成已经承载最终仓内发布真相
    - active `exec-plan` 需要把阶段 A 历史负证据与阶段 B 当前验证结果按 phase 隔离

## closeout 证据

- 功能完成证据：
  - `FR-0011` formal spec / runtime 已由 PR `#169/#184` 合入主干
  - `FR-0010` formal spec / runtime / store bootstrap traceability 已由 PR `#170/#176/#178` 合入主干
  - `FR-0012` formal spec / runtime 已由 PR `#171/#182` 合入主干
  - `FR-0007` 回归基线修复已由 PR `#180` 合入主干
- 阶段 A carrier 证据：
  - `docs/releases/v0.4.0.md`
  - `docs/sprints/2026-S17.md`
  - `docs/decisions/ADR-GOV-0034-v0-4-0-phase-and-release-closeout.md`
  - `docs/exec-plans/GOV-0034-v0-4-0-phase-and-release-closeout.md`
- 发布锚点证据：
  - `v0.4.0` tag 已创建并推送
  - GitHub Release `v0.4.0` 已创建

## 剩余 closeout 动作

- 合入阶段 B metadata-only/docs PR
- 回写并关闭 `#185`
- 补 `#162` 的最终 closeout 评论

## GitHub closeout 工件

- `#185` 正文修正目标：
  - 执行状态改为 `已完成（阶段 A PR / 阶段 B PR 已 MERGED）`
  - 回填两阶段 PR、merge commit、tag 与 GitHub Release
  - 明确本事项负责 `v0.4.0` 的 release carrier、tag 与 GitHub Release 发布
- `#185` 最终评论目标：
  - 汇总阶段 A / 阶段 B PR、tag、GitHub Release 与 merge commit
- `#162` 最终评论目标：
  - 汇总 `#163/#165/#167`、相关 PR、`v0.4.0` tag 与 GitHub Release

## 未决风险

- 若阶段 A 合入后没有立即创建 tag / GitHub Release，仓内 release/sprint 索引会继续滞后于实际版本完成态。
- 若只创建 tag 而不回写 release / sprint / issue closeout metadata，`v0.4.0` 会再次出现“发布锚点已存在，但仓内/issue 真相仍停在前一跳”的分叉。

## 回滚方式

- 仓内回滚：如需回滚，使用独立 revert PR 撤销本事项对 release / sprint 索引、decision 与 exec-plan 的增量修改。
- 仓外回滚：
  - 若阶段 A PR 未合入，恢复 `#185` 正文并停止发布动作
  - 若 tag / GitHub Release 已创建但发现主干事实有误，先修正主干与 GitHub truth，再按独立治理回合决定是否删除 / 重建发布锚点

## 最近一次 checkpoint 对应的 head SHA

- `c9ce7362215c2748df6d7f3c541ae613a62fdeea`
- 说明：该 checkpoint 对应阶段 A carrier 已合入主干且 `v0.4.0` tag / GitHub Release 已建立后的发布完成基线。当前阶段 B 仅回写仓内最终发布真相与 GitHub closeout 元数据，不改写功能或发布锚点语义。
