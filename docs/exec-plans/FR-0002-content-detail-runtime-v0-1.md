# FR-0002-content-detail-runtime-v0-1 执行计划

## 关联信息

- item_key：`FR-0002-content-detail-runtime-v0-1`
- Issue：`#38`
- item_type：`FR`
- release：`v0.1.0`
- sprint：`2026-S15`
- 关联 spec：`docs/specs/FR-0002-content-detail-runtime-v0-1/`
- 关联 decision：`docs/decisions/ADR-0001-governance-bootstrap-contract.md`
- 关联 PR：

## 目标

- 为 `v0.1.0` 启动首个业务 FR 的 formal spec 回合，收口最小 Core/Adapter 契约与双参考适配器验证边界。

## 范围

- 本次纳入：
  - `docs/specs/FR-0002-content-detail-runtime-v0-1/`
  - `docs/exec-plans/FR-0002-content-detail-runtime-v0-1.md`
  - `docs/releases/v0.1.0.md`
  - `docs/sprints/2026-S15.md`
- 本次不纳入：
  - 实现代码
  - 适配器实现
  - HTTP API、队列、资源系统等超范围功能

## 当前停点

- 已创建 GitHub 上位业务 FR `#38` 与 supporting backlog issues `#39` - `#42`。
- 已建立 formal spec、research、risks、contracts 与 release/sprint 聚合入口。
- 当前停在 spec draft 自检完成，准备进入 spec review。

## 下一步动作

- 发起 spec review。
- 根据 review 结论收口 `implementation-ready` 前提。
- 若 review 通过，再拆 implementation 回合。

## 当前 checkpoint 推进的 release 目标

- 为 `v0.1.0` 建立首个业务 formal spec，使“双参考适配器共享 Core 契约”从愿景/路线图进入可审查输入。

## 当前事项在 sprint 中的角色 / 阻塞

- 角色：业务主线 spec kickoff 事项。
- 阻塞：
  - 等待 `spec review` 对当前 formal spec draft 给出结论。

## 已验证项

- `gh issue view 38`
- `gh issue view 39`
- `gh issue view 40`
- `gh issue view 41`
- `gh issue view 42`
- 已完成对 `vision.md`、`docs/roadmap-v0-to-v1.md`、`docs/releases/v0.1.0.md` 的当前阶段边界核对。
- 已完成对参考仓中 xhs/douyin detail 相关模块的只读探索。
- `python3 scripts/docs_guard.py --mode ci`
- `python3 scripts/spec_guard.py --mode ci --all`
- `python3 scripts/governance_gate.py --mode ci --base-sha 9e44783ab67e7b2d0753b3ee3320b922f2e3f471 --head-ref HEAD`

## 未决风险

- 若 `normalized` 字段集定义过大，后续实现可能把平台特有语义误抬升到 Core。
- 若参考适配器实现环境对登录态或签名服务的前置要求判断失真，后续平台联调可能受阻。

## 回滚方式

- 如需回滚，使用独立 revert PR 撤销本事项对 formal spec 套件、release/sprint 索引与 exec-plan 的增量修改。

## 最近一次 checkpoint 对应的 head SHA

- `9e44783ab67e7b2d0753b3ee3320b922f2e3f471`
