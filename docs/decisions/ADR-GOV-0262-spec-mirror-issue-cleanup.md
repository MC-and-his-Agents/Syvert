# ADR-GOV-0262 Keep spec mirror issues closed

## 关联信息

- Issue：`#262`
- item_key：`GOV-0262-spec-mirror-issue-cleanup`
- item_type：`GOV`
- release：`v0.7.0`
- sprint：`2026-S20`

## 背景

`spec_issue_sync.py` 自动维护的 GitHub issue 只用于把仓内 formal spec 的最小索引信息投影到 GitHub。它们不是 Phase、FR 或 Work Item，也不承载执行入口。

当前多个 spec mirror issue 处于 open 状态，导致 GitHub open issue 列表混入不可执行的索引镜像，干扰下一阶段事项识别。

## 决策

- spec mirror issue 必须保持 closed。
- `spec_issue_sync.py` 在新建或更新 mirror issue 后必须立即关闭该 issue。
- mirror 正文必须说明 canonical contract 仍以仓内 `docs/specs/**/spec.md` 为准，且该 issue 不是调度入口。
- 后续进入交付漏斗时，只能使用真实 Phase / FR / Work Item；不得把 spec mirror issue 当作 backlog 或执行入口。

## 影响

- GitHub open issue 列表不再被 spec mirror 索引污染。
- 已关闭的 mirror issue 仍可被同步脚本定位并更新，避免重复创建。
- 若未来需要重新开放 spec mirror issue，必须另建治理事项说明其调度语义。
