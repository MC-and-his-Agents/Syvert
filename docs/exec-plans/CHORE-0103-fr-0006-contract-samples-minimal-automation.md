# CHORE-0103-fr-0006-contract-samples-minimal-automation 执行计划

## 关联信息

- item_key：`CHORE-0103-fr-0006-contract-samples-minimal-automation`
- Issue：`#103`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0006-adapter-contract-test-harness/`
- active Work Item：`CHORE-0103-fr-0006-contract-samples-minimal-automation`

## 目标

- 基于 `FR-0006` spec 的 contract harness 架构，定义 sample 数据结构、四类代表样例，以及与后续验证工具对接的最小 automation 骨架，使 `#103` 能在 `#102/#101` 具体实现交付前就拥有可追踪的 exec-plan。

## 范围

- 本次纳入：
  - 测试侧 contract sample 模型与基础常量
  - 四类 sample 的骨架定义（pass / legal failure / contract violation / execution precondition not met）
  - tests/runtime/contract_harness/ 下的结构化样例集合
  - exec-plan skeleton 记录当前 Work Item 所需的上下文、验证与出口 checkpoint
- 本次不纳入：
  - fake adapter 的 executable 逻辑
  - 验证工具 concrete implementation
  - automation 实际断言或 runner

## 当前停点

- task_id：`issue-103-fr-0006` worktree 目录已准备，下一步先定义 sample 数据模型。
- `tests/runtime/contract_harness/` 目录下尚无具体模块，exec-plan 仍处 draft 模式。

## 下一步动作

1. 定义 sample 描述符（adapter profile / input / verdict）并建立 `CONTRACT_SAMPLES` 常量，确保 sample_id、expected verdict、runtime category、必要 precondition 描述可供后续 harness 读取。
2. 软连 spec 四类场景，确保 pass/legal failure/contract violation/execution precondition not met 四组样例骨架存在，并用注释标注何时由后续 Item 填充具体 adapter responses。
3. 将当前 Work Item 的 review/checkpoints 核心步骤写入 exec-plan（guard commands、验证脚本、后续依赖），为后续 `#103` PR 提供骨干参考。

## 已验证项

- `gh issue view 103 --json number,title,state`
  - 结果：确认 `#103` 已 open 并关联 `FR-0006` harness automation Work Item。
- `python3 scripts/create_worktree.py --issue 103 --class implementation`
  - 结果：should produce `/Users/mc/code/worktrees/syvert/issue-103-fr-0006` (current context).

## 未决风险

- 在 sample 定义阶段依赖 `#102` fake adapter 具体 response shape 可能演进，因此此阶段只记录数据结构与 intent，不在本 exec-plan 中锁定 adapter 实现。
- exec-plan completion 需要 pair with `#101` 验证 tool inputs later;必须保留 placeholder 以便 future PR 绑定 guard commands。

## 回滚方式

- 若 sample skeleton 冲撞 spec semantics，可通过 revert `CHORE-0103` exec-plan 与 `tests/runtime/contract_harness/samples.py` 的 Git commit 实现。

## 最近一次 checkpoint 对应的 head SHA

- 当前仍在 worktree `issue-103-fr-0006` 未提交，checkpoint 暂未记录。
