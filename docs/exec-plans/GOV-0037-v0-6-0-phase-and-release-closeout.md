# GOV-0037 v0.6.0 phase and release closeout 执行计划

## 关联信息

- item_key：`GOV-0037-v0-6-0-phase-and-release-closeout`
- Issue：`#236`
- item_type：`GOV`
- release：`v0.6.0`
- sprint：`2026-S19`
- 关联 spec：无（发布/治理收口事项）
- 关联 decision：`docs/decisions/ADR-GOV-0037-v0-6-0-phase-and-release-closeout.md`
- 状态：`active`

## 目标

- 在不引入新 runtime、formal spec 或测试语义的前提下，通过合法 Work Item `#236` 完成 `v0.6.0` 的 phase / release 发布收口。
- 把 `docs/releases/v0.6.0.md`、`docs/sprints/2026-S19.md`、Git tag、GitHub Release 与 GitHub issue truth 收口到同一条版本 closeout 证据链。

## 范围

- 本次纳入：
  - `docs/exec-plans/GOV-0037-v0-6-0-phase-and-release-closeout.md`
  - `docs/decisions/ADR-GOV-0037-v0-6-0-phase-and-release-closeout.md`
  - `docs/releases/v0.6.0.md`
  - `docs/sprints/2026-S19.md`
- 本次不纳入：
  - 新 runtime / adapter / test 实现
  - `FR-0016` 到 `FR-0019` formal spec 或 requirement 语义改写
  - `v0.7.0` 及后续版本规划推进
  - 阶段 A PR 内建立 tag / GitHub Release
  - 阶段 A PR 内关闭 GitHub Phase `#218`

## 当前停点

- `FR-0016` parent closeout 已由 PR `#248` 合入，merge commit `3c57ec6ce6437b0e810645b104fd85d6bf1235ba`，Issue `#219` 已关闭。
- `FR-0017` parent closeout 已由 PR `#250` 合入，merge commit `394d48a7be861de742aae439c38e18625cc44193`，Issue `#220` 已关闭。
- `FR-0018` parent closeout 已由 PR `#251` 合入，merge commit `7a1439052f85f26ae34e7770dd7de3b4c73f7fb3`，Issue `#221` 已关闭。
- `FR-0019` parent closeout 已由 PR `#253` 合入，merge commit `2413ecc3d8d1811270d45420b91a0ae98af064be`，Issue `#222` 已关闭。
- Git tag `v0.6.0` 当前不存在。
- GitHub Release `v0.6.0` 当前不存在。
- Phase `#218` 仍为 `open`。
- 当前 worktree：`/Users/mc/code/worktrees/syvert/issue-236-v0-6-0`
- 当前主干基线：`2413ecc3d8d1811270d45420b91a0ae98af064be`

## 下一步动作

- 阶段 A：创建 docs PR，建立 release / sprint / decision / exec-plan carrier。
- 阶段 A 合入后 fast-forward main，并在阶段 A merge commit 上创建并推送 `v0.6.0` tag。
- 创建 GitHub Release `v0.6.0`。
- 阶段 B：回写 published truth，合入 metadata-only/docs follow-up。
- 阶段 B 合入后关闭 `#218/#236` 并退役 worktree / branch。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.6.0` 完成“从 FR parent 全部收口到正式发布”的最后一段链路，使 release/sprint 索引、发布锚点与 GitHub closeout 进入一致完成态。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`2026-S19` 的 phase / release closeout Work Item，承接 `FR-0016..FR-0019` parent closeout 后的最终发布动作。
- 位置：本事项是 `v0.6.0` 收口链路的最后一个 Work Item；阶段 A 建立仓内 carrier，阶段 B 建立发布锚点并回写 published truth。
- 阻塞：
  - 阶段 A PR 合入前不得创建 `v0.6.0` tag 或 GitHub Release。
  - 阶段 B 合入并完成 tag / Release / Phase closeout 前，不得声明 `v0.6.0` 完成。

## 已验证项

- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/219`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/220`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/221`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh api repos/MC-and-his-Agents/Syvert/issues/222`
  - 结果：`state=closed`
- `env -u GH_TOKEN -u GITHUB_TOKEN gh release view v0.6.0`
  - 结果：当前不存在 GitHub Release `v0.6.0`
- `git tag --list 'v0.6.0'`
  - 结果：当前未找到 `v0.6.0`

## closeout 证据

- `FR-0016`：formal spec / runtime / parent closeout 已完成，见 `docs/exec-plans/FR-0016-minimal-execution-controls.md`
- `FR-0017`：formal spec / runtime / parent closeout 已完成，见 `docs/exec-plans/FR-0017-runtime-failure-observability.md`
- `FR-0018`：formal spec / HTTP runtime / same-path evidence / parent closeout 已完成，见 `docs/exec-plans/FR-0018-http-task-api-same-core-path.md`
- `FR-0019`：formal spec / gate runtime / source evidence / renderer / parent closeout 已完成，见 `docs/exec-plans/FR-0019-v0-6-operability-release-gate.md`

## 剩余 closeout 动作

- 合入阶段 A docs carrier PR
- 创建并推送 `v0.6.0` tag
- 创建 GitHub Release `v0.6.0`
- 合入阶段 B published-truth follow-up PR
- 回写并关闭 `#218/#236`

## 未决风险

- 若阶段 A 合入后没有立即建立 tag / GitHub Release，仓内 release/sprint 索引仍会滞后于正式发布态。
- 若只建立 tag 而不回写 published truth 与 GitHub issue closeout metadata，`v0.6.0` 会出现“发布锚点已存在，但仓内/issue 真相仍停在前一跳”的分叉。

## 回滚方式

- 仓内回滚：使用独立 revert PR 撤销本事项对 release / sprint 索引、decision 与 exec-plan 的增量修改。
- 仓外回滚：若 tag / GitHub Release 已建立但主干事实有误，先修正主干与 GitHub truth，再按独立治理回合决定是否删除 / 重建发布锚点。

## 最近一次 checkpoint 对应的 head SHA

- `2413ecc3d8d1811270d45420b91a0ae98af064be`
- 说明：该 checkpoint 对应 `FR-0016..FR-0019` parent closeout 全部合入主干、`v0.6.0` 具备正式发布前主干基线。阶段 A carrier、tag / GitHub Release 与阶段 B metadata-only 回写属于该 checkpoint 之后的发布收口动作。
