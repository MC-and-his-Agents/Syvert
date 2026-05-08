# FR-0351 risks

## 风险

- 如果不冻结本 gate，`v1.0.0` 可能在 `v0.9.0` 后继续依赖人工解释，导致 Core stable 标准漂移。
- 如果把真实 provider sample 写成 provider 产品正式支持，会把 Syvert 主仓推向 provider 产品路线。
- 如果把上层应用或 Python package publish 纳入默认 gate，会扩大 `v1.0.0` 范围并阻塞 Core stable。
- 如果只引用 fixture 而没有真实 provider sample evidence，`Adapter + Provider` 兼容性判断仍停留在纸面验证。

## 回滚

- 如本 gate 被证明过宽或过窄，使用独立 spec PR 修改 `FR-0351` formal spec。
- 不通过 runtime PR 隐式改写本 gate。
- 不通过 release closeout PR 临时降低 required gate item。
