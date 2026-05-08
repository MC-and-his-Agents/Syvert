# ADR-CHORE-0352 Record v1.0.0 Core stable release gate formalization

## 关联信息

- item_key：`CHORE-0352-v1-core-stable-release-gate-spec`
- Issue：`#352`
- 上位 Phase：`#350`
- 上位 FR：`#351`
- release：`v1.0.0`
- sprint：`2026-S22`

## 背景

`v0.8.0` 已经完成开放 Adapter / Provider compatibility foundation。`v0.9.0` 的主目标是用真实 provider 样本验证该 foundation。为了让 `v0.9.0` 输出能直接进入 `v1.0.0` 判断，需要先冻结 `v1.0.0` Core stable release gate。

## 决策

- 建立 `FR-0351-v1-core-stable-release-gate` formal spec suite。
- 将 `v1.0.0` gate 明确为 Core stable release gate，而不是上层应用、provider 产品支持或 Python package publish gate。
- 将真实 provider 样本 evidence 明确为 `v1.0.0` required gate input，但不把任何 provider 产品写成正式支持承诺。
- 后续 `v0.9.0` Phase / FR / Work Item 必须消费本 gate 的 `provider_compatibility_sample` 条目。

## 影响

- `v0.9.0` 的推进目标更明确：交付真实 provider 样本 evidence，而不是重新定义 v1.0 标准。
- `v1.0.0` 发布 closeout 可以按 checklist 审查，不再依赖会话上下文。
- Python packaging 仍保持可选 distribution artifact，不成为默认 release gate。
