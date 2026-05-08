# ADR-GOV-0373 v1.1 Operation Taxonomy Release Closeout

## 关联信息

- Issue：`#373`
- item_key：`GOV-0373-v1-1-operation-taxonomy-release-closeout`
- item_type：`GOV`
- release：`v1.1.0`
- sprint：`2026-S23`

## Status

Accepted

## Decision

`v1.1.0` 发布语义固定为 Operation Taxonomy Foundation。该 release 可以新增 taxonomy/admission/validator/consumer foundation，但不能把候选能力族发布为 stable executable runtime capability。

## Rationale

先冻结 operation taxonomy 和 stable lookup，是后续 v1.x 搜索、评论、发布、批量和 dataset 能力进入 Core-facing contract 的前置条件。若在 v1.1.0 直接交付候选 runtime capability，会把 admission gate 与 capability implementation 混在同一发布里，增加 baseline 漂移风险。

## Consequences

- `content_detail_by_url` 仍是唯一 stable runtime operation。
- 候选能力族只能以 `proposed` + `runtime_delivery=false` 出现。
- 后续候选能力升级必须另走 FR、formal spec、contract test 和双参考或等价 evidence。
