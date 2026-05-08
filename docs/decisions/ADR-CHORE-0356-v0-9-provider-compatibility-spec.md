# ADR-CHORE-0356 v0.9.0 provider compatibility spec

## 状态

Accepted

## 背景

`v0.8.0` 已经完成 Adapter / Provider compatibility decision 的 contract foundation。`v1.0.0` release gate 要求 `v0.9.0 provider sample evidence`，但在进入 implementation 前需要先冻结该 evidence 的边界，避免把真实 provider 样本误写成 provider 产品支持、selector / fallback 或上层应用能力。

## 决策

- 为 `v0.9.0` 创建 `FR-0355` formal spec suite。
- 把真实 provider sample evidence 定义为 release closeout evidence contract，而不是新的 Core public contract。
- 要求 implementation 使用非仓内 native provider 的 external sample，并覆盖 `matched`、`unmatched`、`invalid_contract`。
- 要求 provider sample evidence 明确 `provider_support_claim=false`。
- 保持 spec 与 implementation PR 分离；`#356` 不修改 runtime、tests、scripts 或 CI。

## 后果

- 后续 implementation Work Item 可以直接消费 `FR-0355`，不用在实现 PR 中重新解释 `v0.9.0` 的 evidence 语义。
- `v1.0.0` closeout 可以通过 `FR-0351` 消费 `FR-0355` 的 provider sample evidence。
- 若后续发现 external provider sample 需要改变 runtime contract，必须另建实现或 spec follow-up，不得在 release closeout 中静默扩范围。
