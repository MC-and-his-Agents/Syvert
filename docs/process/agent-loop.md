# Syvert Agent Loop

本文件定义长任务唯一运行协议：

`kickoff -> checkpoint -> compact -> resume -> handoff -> merge-ready`

## kickoff

1. 绑定 Issue 与阶段边界。
2. 确认输入工件：formal spec 或 bootstrap contract。
3. 初始化或更新 `exec-plan` 与 `TODO.md`。

## checkpoint

- 最小频率：每完成一组可验证改动后更新一次。
- 必填内容：
  - 当前停点
  - 下一步动作
  - 已验证项
  - 未决风险
  - 当前 head SHA

## compact

- 仅允许压缩已完成且已入库的上下文。
- 不允许压缩未落盘前提、未关闭风险、未验证结论。

## resume

- 从最近一次 checkpoint 恢复。
- 若 head SHA 变化，必须先刷新风险与验证状态，再继续执行。

## handoff

- 更新 `TODO.md` 与 `exec-plan` 到可恢复状态。
- 明确未决风险与阻塞项。

## merge-ready

- 已满足 `code_review.md` 定义的 merge gate。
- 可通过 `python3 scripts/governance_status.py` 输出当前状态面进行核对。

## `exec-plan` 与 `TODO.md` 职责边界

- `exec-plan`：长任务执行细节与恢复上下文。
- `TODO.md`：事项级状态、检查清单、停点与下一步。
- `TODO.md` 不承载完整长会话细节。
