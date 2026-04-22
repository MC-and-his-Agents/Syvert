# ADR-GOV-0035 Align Syvert top-level positioning with the stable substrate for internet operations

## 关联信息

- Issue：`#205`
- item_key：`GOV-0035-top-level-positioning-alignment`
- item_type：`GOV`
- release：`v0.5.0`
- sprint：`2026-S18`

## 背景

当前仓库的顶层权威文档仍把 Syvert 定义为“采集底座”，并把主要价值表述为“平台接入”与“采集任务”的统一承载。

这与当前已经收敛出来的产品边界存在偏差：

- Syvert 不应被长期限定为只读采集场景；它应承载读、写与其他受控互联网操作。
- Syvert 的抽象对象不应被限定为内容平台、账号驱动站点或浏览器路径；站点、接口与其他互联网资源都可能成为适配目标。
- 当前 `v0.x` 的 `content_detail_by_url` 与双参考适配器路径只是验证切片，不应被误读为长期能力上限。

如果继续保留“采集底座”的顶层叙事，后续关于共享输入模型、结果契约和资源语义的 formal spec 讨论会持续混淆“长期定位”和“当前验证切片”两层语义。

## 决策

- 使用单一治理 Work Item `#205 / GOV-0035-top-level-positioning-alignment` 收口本轮顶层定位修订。
- Syvert 的顶层定位统一收敛为：`Syvert 是一个统一承载和治理互联网操作任务及其资源的稳定底座。`
- 本轮只允许修改 `AGENTS.md`、`vision.md`、`docs/roadmap-v0-to-v1.md` 以及当前治理回合所需的 bootstrap decision / active exec-plan。
- 本轮不改写任何 formal spec、历史 release/sprint 索引、研究材料或 runtime / adapter 实现。
- 现有 `raw payload` / `normalized result`、`CollectionPolicy`、`content_detail_by_url` 等语义继续作为当前验证切片或既有 formal spec 的真相保留；若后续需要把这些语义扩展为更一般的互联网操作模型，必须进入独立 formal spec 回合。

## 影响

- `AGENTS.md`、`vision.md` 与 `docs/roadmap-v0-to-v1.md` 的顶层叙事会对齐到同一产品边界。
- `v0.x` 当前验证路径会被保留为阶段切片，而不再被误读为 Syvert 的长期产品定义。
- 后续 formal spec 若要从采集导向扩展到更一般的互联网操作语义，可以在不反复争论顶层定位的前提下进行独立审查。
