# GOV-0034-v0.4.0-phase-and-release-closeout 执行计划

## 关联信息

- item_key：`GOV-0034-v0-4-0-phase-and-release-closeout`
- Issue：`#185`
- item_type：`GOV`
- release：`v0.4.0`
- sprint：`2026-S17`
- 关联 spec：无（发布/治理收口事项）
- 关联 decision：`docs/decisions/ADR-GOV-0034-v0-4-0-phase-and-release-closeout.md`
- 关联 PR：`#186`
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

- `origin/main@d2be4bf90dd7d26e389abee5fd93e5ceb52a737e` 已包含 `v0.4.0` 所需的全部 formal spec、runtime、reference adapter 收口与回归修复：PR `#169/#170/#171/#176/#178/#180/#182/#184`。
- `#162` 已关闭，`#163/#165/#167` 及其下属 Work Item 也已关闭，`v0.4.0` 的功能与 FR closeout 目标已经完成。
- 当前分支已补齐 `docs/releases/v0.4.0.md`、`docs/sprints/2026-S17.md`、本事项 decision 与 active exec-plan，阶段 A carrier 已形成独立 docs checkpoint。
- 主干当前仍缺 `v0.4.0` git tag、GitHub Release 与阶段 A carrier 合入后的仓内发布索引。
- `#185` 已建立为承接 `v0.4.0` phase / release closeout 的合法治理 Work Item。
- 当前执行现场为独立 worktree：`/Users/mc/code/worktrees/syvert/issue-185-v0-4-0`，当前分支为 `issue-185-v0-4-0`。
- 阶段 A docs PR `#186` 已创建，当前回合正在补齐 review carrier 后重新进入 guardian / merge gate。
- 本事项按同一 Work Item 的两阶段模型推进：当前阶段 A 负责建立仓内 carrier；阶段 A 合入后，阶段 B 负责建立发布锚点并回写最终发布真相。

## 下一步动作

- 同步 PR `#186` 的审查载体与验证信息。
- 在当前 head 上完成 guardian 与 merge gate，并合入阶段 A。
- 基于阶段 A 合入后的主干提交创建并推送 annotated tag `v0.4.0`，随后创建 GitHub Release `v0.4.0`。
- 以同一 Work Item 发起阶段 B metadata-only/docs PR，把 release / sprint 索引与本 exec-plan 从“待发布锚点”同步到最终发布完成真相。
- 合并阶段 B 后回写并关闭 `#185`，并补 `#162` 的最终 closeout 评论。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.4.0` 完成“从功能收口到正式发布”的最后一段链路，使 release/sprint 索引、发布锚点与 GitHub closeout 进入一致完成态。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`v0.4.0` 的 phase / release 发布 closeout Work Item。
- 阻塞：
  - `#185` 之外不存在合法执行入口，tag / Release 不能直接挂到 Phase 或 FR 容器上执行。
  - 发布锚点必须等阶段 A 文档 PR 合入主干后才能建立，避免 tag / Release 指向未入主干的 carrier。

## 已验证项

- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 162 --json state`
  - 结果：`#162` 为 `CLOSED`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 163 --json state`
  - 结果：`#163` 为 `CLOSED`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 165 --json state`
  - 结果：`#165` 为 `CLOSED`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 167 --json state`
  - 结果：`#167` 为 `CLOSED`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh issue view 185 --json state`
  - 结果：`#185` 为 `OPEN`
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
- 当前缺失的发布锚点证据：
  - `v0.4.0` tag 尚未创建
  - GitHub Release `v0.4.0` 尚未创建

## 剩余 closeout 动作

- 合入阶段 A docs PR
- 创建并推送 tag `v0.4.0`
- 创建 GitHub Release `v0.4.0`
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

- `ac557837e5284c31043bc3527f1bf31c002a2bf9`
- 说明：该 checkpoint 在 `v0.4.0` 发布前基线之上补齐了阶段 A release/sprint carrier、decision 与 active exec-plan。当前 head 只建立发布入口与治理证据，不改写既有功能 checkpoint 语义。
