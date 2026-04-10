# Syvert Agent Loop

本文件定义长任务唯一运行协议：

`kickoff -> checkpoint -> compact -> resume -> handoff -> merge-ready`

## kickoff

1. 绑定当前 Work Item 的事项上下文：`Issue`、`item_key`、`item_type`、`release`、`sprint` 与上位 Phase / FR 边界。
2. 确认当前独立现场与事项上下文匹配：worktree 仍由当前 Work Item 的 `Issue` 生成，事项上下文不改变现有现场模型。
3. 确认输入工件：若 formal spec 已存在，则使用绑定 FR 的 formal spec；若仍处于治理 bootstrap 例外，则使用 `Issue + decision + exec-plan`。
4. 初始化或更新当前 Work Item 的 `exec-plan`；若 formal spec 已存在，再在绑定 FR 的 `TODO.md` 中回写当前 active Work Item 指针与状态。

## checkpoint

- 最小频率：每完成一组可验证改动后更新一次。
- 必填内容：
  - 当前 Work Item 事项上下文
  - 当前停点
  - 下一步动作
  - 当前改动推进了哪个 `release` 目标
  - 当前事项在 `sprint` 中的角色、位置或阻塞关系
  - 已验证项
  - 未决风险
  - 最近一次 checkpoint 对应的 head SHA
- 只有当执行回合显式形成新的 checkpoint 时，才推进该 head SHA。
- review 结论、GitHub checks、PR 关联等审查态信息的补充，不单独构成新的 checkpoint。

## compact

- 仅允许压缩已完成且已入库的上下文。
- 不允许压缩未落盘前提、未关闭风险、未验证结论。
- 不允许压缩未落盘的 `release` / `sprint` 绑定与事项角色判断。

## resume

- 从最近一次 checkpoint 恢复。
- 若 head SHA 变化且形成新的 checkpoint，必须先刷新风险与验证状态，再继续执行。
- 恢复前必须确认当前独立现场与当前 Work Item 事项上下文仍匹配；若 `release`、`sprint` 或事项角色变化，必须先更新 `exec-plan`，并在 formal spec 已存在时同步更新 `TODO.md`。

## handoff

- 更新 `exec-plan` 到可恢复状态；若 formal spec 已存在，再同步更新 `TODO.md`。
- 明确未决风险与阻塞项。
- 明确下一个 agent 进入当前现场后所需的 Work Item 事项上下文，以及该事项对 `release` 目标的当前推进状态。

## merge-ready

- 已满足 `code_review.md` 定义的 merge gate。
- 可通过 `python3 scripts/governance_status.py` 输出当前状态面进行核对。
- 核对 `item_context` 段时，应确认 `Issue`、`item_key`、`item_type`、`release`、`sprint` 与 active `exec-plan` 一致。

## `exec-plan` 与 `TODO.md` 职责边界

- `exec-plan`：当前 Work Item 的长任务执行细节、事项上下文与恢复上下文。
- `TODO.md`：当 formal spec 已存在时，作为绑定 FR 的 formal spec 套件中的 FR 级状态总表、当前 active Work Item 指针、检查清单、停点与下一步。
- `TODO.md` 不承载完整长会话细节。
