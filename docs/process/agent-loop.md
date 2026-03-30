# Syvert Agent Loop

本文件定义长任务唯一运行协议：

`kickoff -> checkpoint -> compact -> resume -> handoff -> merge-ready`

## kickoff

1. 绑定事项上下文：`Issue`、`item_key`、`item_type`、`release`、`sprint` 与阶段边界。
2. 确认当前独立现场与事项上下文匹配：worktree 仍由 `Issue` 生成，事项上下文不改变现有现场模型。
3. 确认输入工件：formal spec 或 bootstrap contract。
4. 初始化或更新 `exec-plan` 与 `TODO.md`。

## checkpoint

- 最小频率：每完成一组可验证改动后更新一次。
- 必填内容：
  - 当前事项上下文
  - 当前停点
  - 下一步动作
  - 当前改动推进了哪个 `release` 目标
  - 当前事项在 `sprint` 中的角色、位置或阻塞关系
  - 已验证项
  - 未决风险
  - 最近一次 checkpoint 对应的 head SHA

## compact

- 仅允许压缩已完成且已入库的上下文。
- 不允许压缩未落盘前提、未关闭风险、未验证结论。
- 不允许压缩未落盘的 `release` / `sprint` 绑定与事项角色判断。

## resume

- 从最近一次 checkpoint 恢复。
- 若 head SHA 变化且形成新的 checkpoint，必须先刷新风险与验证状态，再继续执行。
- 恢复前必须确认当前独立现场与事项上下文仍匹配；若 `release`、`sprint` 或事项角色变化，必须先更新 `exec-plan` 与 `TODO.md`。

## handoff

- 更新 `TODO.md` 与 `exec-plan` 到可恢复状态。
- 明确未决风险与阻塞项。
- 明确下一个 agent 进入当前现场后所需的事项上下文，以及该事项对 `release` 目标的当前推进状态。

## merge-ready

- 已满足 `code_review.md` 定义的 merge gate。
- 可通过 `python3 scripts/governance_status.py` 输出当前状态面进行核对。

## `exec-plan` 与 `TODO.md` 职责边界

- `exec-plan`：长任务执行细节、事项上下文与恢复上下文。
- `TODO.md`：事项级状态、检查清单、停点与下一步。
- `TODO.md` 不承载完整长会话细节。
