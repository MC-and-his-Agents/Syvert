# FR-0006 contracts

本目录只记录 `FR-0006` formal spec 需要冻结的稳定 contract 边界，不定义具体实现目录结构。

## 1. harness contract

- harness 的职责是以受控样例驱动 Core 经过标准 adapter 宿主路径执行 contract 验证。
- harness 的验证对象是共享 adapter contract 的运行时语义，不是平台抓取正确性。
- harness 必须能观测并判定：
  - success envelope 满足 contract，且同时具备 `raw payload` 与 `normalized result`
  - failed envelope 走统一失败处理
  - adapter 返回非法结果时产生 contract violation
  - adapter 声明与实际行为不一致时产生 contract violation
  - 样例在进入 adapter 执行前即不满足前置条件时，验证工具产出 `执行前置不满足`

## 2. fake adapter contract

- fake adapter 是 contract test double，不是参考适配器、也不是平台模拟器。
- fake adapter 只需提供驱动 contract 验证所必需的最小行为：
  - capability 声明
  - 受控成功返回
  - 受控失败返回
  - 受控非法返回
- fake adapter 不承载真实平台 URL 解析、签名、Cookie、网络请求或页面解析逻辑。

## 3. validation tool contract

- 验证工具负责组织样例、触发 harness 执行并输出结果。
- 验证工具至少输出四类可判定结果：
  - 通过
  - 合法失败
  - contract violation
  - 执行前置不满足
- `contract violation` 是验证工具层分类，表示观测到的运行结果不满足已批准 contract；它不是新的运行时 `error.category`。
- 对于已按 `FR-0005` 上位 contract 返回的合法失败 envelope，验证工具必须归类为“合法失败”，而不是 `contract violation`。
- `执行前置不满足` 只覆盖验证工具或 harness 在进入 Core 执行前即可判定的测试期前提缺失；它不是运行时 envelope，也不替代 `invalid_input`、`unsupported`、`runtime_contract` 或 `platform`。
- 验证工具不重新定义 adapter contract 本身；它只消费已批准的 formal spec。

## 4. boundary contract

- 本 FR 产物可作为真实平台测试、参考适配器回归与版本 gate 的下游输入。
- 本 FR 不定义这些下游流程的编排、放行条件或 GitHub/CI 接线方式。
