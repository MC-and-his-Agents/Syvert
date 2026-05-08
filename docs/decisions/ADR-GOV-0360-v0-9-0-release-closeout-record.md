# ADR-GOV-0360 Record v0.9.0 release closeout carrier and published-truth plan

## 关联信息

- Issue：`#360`
- item_key：`GOV-0360-v0-9-0-release-closeout-record`
- item_type：`GOV`
- release：`v0.9.0`
- sprint：`2026-S22`
- Parent Phase：`#354`
- Parent FR：`#355`

## 背景

`v0.9.0` 的核心 implementation truth 已合入 main：

- `#356 / PR #357` 交付 `FR-0355` formal spec，merge commit `5d505179f3ea4d0508e913e407f39b4c73ba8874`。
- `#358 / PR #359` 交付 external provider sample evidence，merge commit `ecfc3bf53299191e42c13c5b1c6578fd90aa84b6`。
- main 已包含可被 `FR-0351:provider_compatibility_sample` 消费的 provider compatibility sample evidence。

仍需补齐 release closeout：release index、sprint index、closeout evidence、annotated tag、GitHub Release、published truth carrier 以及 Phase / FR / Work Item GitHub 状态对账。

## 决策

- 使用治理 Work Item `#360 / GOV-0360-v0-9-0-release-closeout-record` 承接 `v0.9.0` release closeout carrier 与 published truth 锚点。
- 本事项不新增 runtime、formal spec、Adapter、Provider 或 Python packaging 语义。
- 本事项采用串行 closeout：
  - 阶段 A：通过 docs PR 建立 release closeout carrier，包括 release index、sprint index、exec-plan、ADR 与 evidence artifact。
  - 发布锚点：阶段 A 合入后，在阶段 A merge commit 上创建 `v0.9.0` annotated tag 和 GitHub Release。
  - 阶段 B：通过 follow-up docs PR 回写 tag / GitHub Release published truth，并在合入后关闭 `#354/#355/#360`。

## 影响

- `v0.9.0` 从“implementation evidence 已合入”推进到“release truth 可版本化、可复验”。
- `v1.0.0` Core stable release gate 可消费 `v0.9.0` 的 provider compatibility sample evidence。
- 本事项不声明任何指定 provider 产品正式支持，不引入 Core provider registry、provider selector、fallback、ranking 或 marketplace。
