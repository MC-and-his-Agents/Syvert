# dual-reference-resource-capability-evidence contract（v0.5.0）

## 接口名称与版本

- 接口名称：`dual-reference-resource-capability-evidence`
- contract 版本：`v0.5.0` capability vocabulary baseline；`v0.8.0` profile evidence extension
- 作用：定义双参考适配器资源能力证据记录的最小 carrier、批准规则、`FR-0013 / FR-0014` 可消费的资源能力词汇边界，以及 `FR-0027` 可消费的 profile approval proof

## 证据记录结构

- `DualReferenceResourceCapabilityEvidenceRecord`
  - 必填字段：
    - `adapter_key`
    - `capability`
    - `execution_path`
    - `resource_signals`
    - `candidate_abstract_capability`
    - `shared_status`
    - `evidence_refs`
    - `decision`
  - 字段约束：
    - `adapter_key`：当前只允许 `xhs`、`douyin`
    - `capability`：当前双参考基线只允许 `content_detail`
    - `execution_path`：至少必须稳定表达 `target_type` 与 `collection_mode`
    - `resource_signals`：只允许观测事实，不允许 provider 选择、排序、fallback 或技术偏好
    - `candidate_abstract_capability`：资源能力候选标识
    - `shared_status`：只允许 `shared`、`adapter_only`、`rejected`
    - `evidence_refs`：非空、去重，且必须能回指 `research.md` 中的稳定 evidence registry 条目
    - `decision`：只允许 `approve_for_v0_5_0`、`keep_adapter_local`、`reject_for_v0_5_0`
  - 映射约束：
    - `shared` 只能映射到 `approve_for_v0_5_0`
    - `adapter_only` 只能映射到 `keep_adapter_local`
    - `rejected` 只能映射到 `reject_for_v0_5_0`
- `ResourceRequirementProfileEvidenceRecord`
  - 必填字段：
    - `profile_ref`
    - `capability`
    - `execution_path`
    - `resource_dependency_mode`
    - `required_capabilities`
    - `reference_adapters`
    - `shared_status`
    - `decision`
    - `evidence_refs`
  - 字段约束：
    - `profile_ref`：非空、稳定、唯一
    - `capability`：当前只允许 `content_detail`
    - `execution_path`：当前固定为 `operation=content_detail_by_url`、`target_type=url`、`collection_mode=hybrid`
    - `resource_dependency_mode`：只允许 `none`、`required`
    - `required_capabilities`：mode=`none` 时为空；mode=`required` 时非空、去重
    - `reference_adapters`：非空、去重；shared profile 必须覆盖 `xhs` 与 `douyin`
    - `shared_status`：只允许 `shared`、`adapter_only`、`rejected`
    - `decision`：只允许 `approve_profile_for_v0_8_0`、`keep_adapter_local`、`reject_profile_for_v0_8_0`
    - `evidence_refs`：非空、去重，且必须回指 `research.md` 中稳定 evidence registry 条目
  - 映射约束：
    - `shared` 只能映射到 `approve_profile_for_v0_8_0`
    - `adapter_only` 只能映射到 `keep_adapter_local`
    - `rejected` 只能映射到 `reject_profile_for_v0_8_0`

## 批准词汇投影

- `FR-0015` 是 `v0.5.0` 共享资源能力词汇的唯一批准入口
- 能力只有在满足以下条件时才允许被下游 FR 消费：
  - 对同一 `candidate_abstract_capability`，`xhs` 与 `douyin` 都有稳定证据记录
  - 两侧证据都指向可比较的 `execution_path`
  - 两侧记录都满足 `shared_status=shared`
  - 两侧记录都满足 `decision=approve_for_v0_5_0`
- 当前唯一批准词汇：
  - `account`
  - `proxy`
- 下游消费约束：
  - `FR-0013` 只能在 `required_capabilities[]` 中使用上述批准标识
  - `FR-0014` 只能匹配上述批准标识
  - 下游 FR 不得通过实现或 matcher 输入反向新增能力名

## `FR-0027` profile proof 投影

- `ApprovedSharedResourceRequirementProfileEvidenceEntry` 只允许由 `shared + approve_profile_for_v0_8_0` 的 `ResourceRequirementProfileEvidenceRecord` 投影产生。
- 当前唯一批准 shared profile：
  - `fr-0027:profile:content-detail-by-url-hybrid:account-proxy`
  - `fr-0027:profile:content-detail-by-url-hybrid:account`
- 当前禁止进入 shared declaration 的 profile：
  - `fr-0027:profile:content-detail-by-url-hybrid:proxy`
  - `fr-0027:profile:content-detail-by-url-hybrid:none`
  - `fr-0027:profile:content-detail-by-url-hybrid:douyin-account-private-material`
- `FR-0027` declaration profile 的 `evidence_refs` 只能引用上述 approved shared profile proof；不得引用 `adapter_only`、`rejected` profile 或 capability-level evidence record。

## research 入口与证据引用

- `research.md` 必须至少保留以下章节：
  - 共性资源语义
  - 单平台特例
  - 被拒绝的抽象候选
  - `v0.8.0` profile evidence 判定口径
  - 冻结的 `v0.8.0` profile evidence truth
- `evidence_refs` 的合法来源：
  - 仓内稳定代码路径、研究条目或回归基线条目
  - 能被 future review 复验的静态引用
- `evidence_refs` 的非法来源：
  - 会话内口头描述
  - 一次性人工笔记
  - 无稳定标识的截图、日志片段或临时命令输出

## 禁止的抽象方向

- 不允许把以下内容直接批准为共享能力：
  - Playwright / CDP / Chromium / browser tab 等技术实现名词
  - `verify_fp`、`ms_token`、`webid`、`a_bogus`、`xsec_token`、`xsec_source` 等平台私有 token
  - `cookies`、`user_agent` 等 `account.material` 内部字段
  - `sign_base_url`、`browser_state` 等重技术绑定候选
- 这些候选必须被写成 `adapter_only` 或 `rejected`，而不是留给下游事项自行解释

## 向后兼容约束

- 本 FR 不改写 `FR-0010` 的 `account / proxy` 资源类型语义
- 本 FR 不改写 `FR-0012` 的 Core 注入 boundary
- 若未来需要新增 `account / proxy` 之外的共享能力，必须通过新的双参考证据与新的 formal spec closeout 明确收口
