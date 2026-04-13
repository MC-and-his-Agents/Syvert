# CHORE-0069-fr-0005-standardized-error-model 执行计划

## 关联信息

- item_key：`CHORE-0069-fr-0005-standardized-error-model`
- Issue：`#69`
- item_type：`CHORE`
- release：`v0.2.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- 关联 decision：
- 关联 PR：

## 目标

- 在 `FR-0005` 范围内落地标准化错误模型，把 Core / Adapter 的失败路径统一映射到 `invalid_input`、`unsupported`、`runtime_contract`、`platform` 四类运行时语义。

## 范围

- 本次纳入：
  - `syvert/runtime.py`
  - `syvert/cli.py`
  - `tests/runtime/test_runtime.py`
  - `tests/runtime/test_executor.py`
  - `tests/runtime/test_cli.py`
  - `docs/releases/v0.2.0.md`
  - `docs/sprints/2026-S15.md`
  - 本 exec-plan
- 本次不纳入：
  - adapter registry materialization / discovery / registration
  - fake adapter、harness、validator、version gate
  - `FR-0004` 的输入建模语义改写
  - 平台适配器内部平台逻辑

## 当前停点

- `FR-0005` formal spec 已由 PR `#78` 合入主干，`#69` 仍为 open Work Item，尚无 implementation PR。
- 当前主干运行时仅实做 `runtime_contract` / `platform` 两类失败分类，`invalid_input` / `unsupported` 尚未进入统一实现路径。
- 当前 `execute_task()` 仍把 adapter 不存在、capability 不支持、非法请求形状等路径大多打成 `runtime_contract`，与 `FR-0005` formal spec 不一致。

## 下一步动作

- 为 runtime / CLI 新增 `invalid_input` 与 `unsupported` 错误 helper，并把现有失败分支重映射到 formal spec 指定分类。
- 补齐并更新 runtime / executor / CLI 回归测试。
- 运行 implementation 门禁，创建 `#69` 对应 PR。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.2.0` 把共享错误分类从“能跑即可”推进到“契约可验证”，为后续 `#70` registry contract 与 `FR-0006/#0007` 的上层复用提供稳定失败语义。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：`FR-0005` 的第一个 implementation Work Item，负责先把错误模型从 formal spec 落到主干运行时。
- 阻塞：
  - 不得把 adapter registry、harness、gate、fake adapter 或额外 FR 范围并入当前回合。

## 已验证项

- 已阅读：`AGENTS.md`
- 已阅读：`WORKFLOW.md`
- 已阅读：`docs/AGENTS.md`
- 已阅读：`docs/process/delivery-funnel.md`
- 已阅读：`spec_review.md`
- 已阅读：`code_review.md`
- 已阅读：`docs/specs/FR-0005-standardized-error-model-and-adapter-registry/`
- `gh issue view 69 --repo MC-and-his-Agents/Syvert`
- `python3 scripts/create_worktree.py --issue 69 --class implementation`
  - 结果：已创建 worktree `/Users/mc/code/worktrees/syvert/issue-69-task`

## 未决风险

- 若把 adapter target / collection admission 的失败误判为 `unsupported`，会模糊 `invalid_input` 与 “adapter 前置输入约束不满足” 的 spec 边界。
- 若在本回合顺手引入 registry 结构，会与 `#70` 的职责切分串线。
- 若 CLI 参数错误仍保留为 `runtime_contract`，则主干 CLI 与 formal spec 的 `invalid_input` 边界不一致。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 runtime、CLI、tests、release/sprint 索引与本 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `bb0f4af77f8ba54fff43290ff8c98a903d35a4ed`
