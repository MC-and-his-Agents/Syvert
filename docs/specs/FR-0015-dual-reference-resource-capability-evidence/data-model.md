# FR-0015 数据模型

## 实体清单

- 实体：`DualReferenceResourceCapabilityEvidenceRecord`
  - 用途：表达某个双参考适配器在特定执行路径上，对某个候选资源能力给出的正式证据记录
- 实体：`ExecutionPathDescriptor`
  - 用途：表达证据成立的执行路径边界，避免把不相容路径压平为同一条 evidence truth
- 实体：`ApprovedResourceCapabilityVocabularyEntry`
  - 用途：表达由多条 `DualReferenceResourceCapabilityEvidenceRecord` 投影出的、可被 `FR-0013 / FR-0014` 消费的批准能力词汇条目

## 关键字段

- `DualReferenceResourceCapabilityEvidenceRecord`
  - `adapter_key`
    - 约束：非空字符串；在 `v0.5.0` 只允许 `xhs` 或 `douyin`
  - `capability`
    - 约束：非空字符串；表达 adapter-facing capability family；当前双参考基线只允许 `content_detail`
  - `execution_path`
    - 约束：必须满足 `ExecutionPathDescriptor` contract
  - `resource_signals`
    - 约束：非空、JSON-safe 的事实集合；只允许记录观察到的资源事实，不得混入 provider 选择、调度打分或技术偏好
  - `candidate_abstract_capability`
    - 约束：非空字符串；表达待批准、`adapter_only` 或 `rejected` 的资源能力候选标识
  - `shared_status`
    - 约束：只允许 `shared`、`adapter_only`、`rejected`
  - `evidence_refs`
    - 约束：非空、去重字符串数组；每个值都必须能回指 `research.md` 中的稳定 evidence registry 条目
  - `decision`
    - 约束：只允许 `approve_for_v0_5_0`、`keep_adapter_local`、`reject_for_v0_5_0`
    - 映射约束：`shared -> approve_for_v0_5_0`、`adapter_only -> keep_adapter_local`、`rejected -> reject_for_v0_5_0`
- `ExecutionPathDescriptor`
  - `target_type`
    - 约束：非空字符串；在当前双参考基线中固定为 `url`
  - `collection_mode`
    - 约束：非空字符串；在当前双参考基线中固定为 `hybrid`
  - `operation`
    - 约束：可选非空字符串；当前基线允许记录为 `content_detail_by_url`，用于把 adapter-facing family 与当前 runtime 共享执行入口对齐
- `ApprovedResourceCapabilityVocabularyEntry`
  - `capability_id`
    - 约束：非空字符串；只能来自 `DualReferenceResourceCapabilityEvidenceRecord.candidate_abstract_capability`
  - `approval_basis_evidence_refs`
    - 约束：非空、去重字符串数组；必须能证明 `xhs` 与 `douyin` 在同类路径上都给出 `shared + approve_for_v0_5_0`
  - `status`
    - 约束：在本实体中固定为 `approved`

## 批准词汇表（v0.5.0 冻结基线）

- `ApprovedResourceCapabilityVocabularyEntry(capability_id=account)`
  - 语义：Core 可以注入供 adapter 消费的最小受管账号材料 carrier
  - `approval_basis_evidence_refs`：
    - `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`
    - `fr-0015:xhs:content-detail:url:hybrid:account-material`
    - `fr-0015:douyin:content-detail:url:hybrid:account-material`
- `ApprovedResourceCapabilityVocabularyEntry(capability_id=proxy)`
  - 语义：当前共享执行路径需要最小受管代理能力前提
  - `approval_basis_evidence_refs`：
    - `fr-0015:runtime:content-detail-by-url-hybrid:requested-slots`
    - `fr-0015:regression:xhs:managed-proxy-seed`
    - `fr-0015:regression:douyin:managed-proxy-seed`

## 明确不批准的候选方向

- `verify_fp`、`ms_token`、`webid`
  - 约束：仅出现在抖音账号材料；属于 `adapter_only`
- `sign_base_url`、`browser_state`
  - 约束：技术绑定过重；属于 `rejected`
- `cookies`、`user_agent`
  - 约束：属于 `account` 材料内部字段，不单独提升为共享能力名；属于 `rejected`
- `a_bogus`、`xsec_token`、`xsec_source`
  - 约束：平台私有 token 或 URL 解析细节；不得进入共享能力词汇

## 生命周期

- 创建：
  - 当某个资源能力候选需要进入 `v0.5.0` 讨论时，必须先以 `DualReferenceResourceCapabilityEvidenceRecord` 建档
- 更新：
  - 当 evidence review 确认某个候选已满足双参考共享条件时，可把对应 candidate capability 投影为 `ApprovedResourceCapabilityVocabularyEntry`
  - 若候选被判定为单平台私有或技术绑定，则保持在 `adapter_only` / `rejected`，不得投影到批准词汇表
- 失效/归档：
  - 本 FR 不定义 evidence registry 的持久化后端或归档策略；只冻结 formal carrier 与批准规则
