# FR-0007 契约说明

本事项不冻结具体脚本接口，但会冻结以下版本 gate 契约：

1. 职责边界契约
   - `FR-0006` 负责 contract harness、fake adapter 与验证基座
   - `FR-0007` 负责版本 gate 对 harness 结果的消费，以及双参考适配器回归检查与平台泄漏检查的版本级叠加
   - `FR-0006` 的结论不得单独替代 `FR-0007` 的版本完成判定

2. 版本 gate 组成契约
   - mandatory trigger：
   - 结束当前版本回合前
   - 进入下一版本前
   - required gate conclusions：
   - contract harness 结果消费结论
   - 双参考适配器回归结论
   - 平台泄漏检查结论

3. gate 对象契约
   - 双参考适配器集合在 `v0.2.0` 范围内固定为 adapter registry 中登记的小红书与抖音参考适配器
   - 若后续版本要调整 reference pair，必须通过新的 formal spec 明确冻结
   - gate 输入必须遵循共享输入模型
   - gate 成功/失败判定必须兼容共享错误模型与 registry 语义

4. 失败语义契约
   - 任一必选 gate 未执行、失败、结果不完整、结论不可信或不可追溯时，版本 gate 一律 fail-closed
   - 最小完整性判据至少包括：当前版本标识明确、reference pair 覆盖证明完整、三类检查结论齐备且可追溯
   - 失败来源至少能区分 harness、真实参考适配器回归、平台泄漏三类

5. 平台泄漏边界契约
   - 允许平台语义留在 adapter 私有实现与平台研究文档
   - 禁止平台语义进入 Core 主路径、共享输入模型、共享错误模型、adapter registry 共享契约、共享结果 contract（含 `raw` / `normalized` 的共享结果语义）与 gate 共享判定逻辑

如需增加更细的 gate payload 结构、结果格式或执行协议，应在后续实现 Work Item 中补充独立契约文档，并保持与本 requirement 一致。
