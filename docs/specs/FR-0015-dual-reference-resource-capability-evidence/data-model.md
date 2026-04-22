# FR-0015 数据模型

## 实体清单

- 实体：`DualReferenceResourceCapabilityEvidenceRecord`
  - 用途：表达单条 reference adapter 资源能力证据记录，是 `FR-0015` 的 canonical evidence carrier
- 实体：`ResourceSignal`
  - 用途：表达某条执行路径上观察到的资源语义信号，用于支持共享 / adapter-only / rejected 决策
- 实体：`ApprovedAbstractCapabilityVocabularyEntry`
  - 用途：表达 `v0.5.0` 已批准的共享资源能力标识及其语义约束

## 关键字段

- `DualReferenceResourceCapabilityEvidenceRecord`
  - `adapter_key`
    - 约束：非空字符串；当前只允许 `xhs` 或 `douyin`
  - `capability`
    - 约束：非空字符串；当前 evidence baseline 只允许 `content_detail_by_url`
  - `execution_path`
    - 约束：非空字符串；当前 evidence baseline 固定为 `hybrid_content_detail_by_url`
  - `resource_signals`
    - 约束：非空数组；元素必须满足 `ResourceSignal` contract；用于解释当前候选抽象为何共享、为何只应留在 adapter 私有边界，或为何必须被拒绝
  - `candidate_abstract_capability`
    - 约束：非空字符串；表示当前记录正在审查的候选抽象能力标识
  - `shared_status`
    - 约束：只允许 `shared`、`adapter_only`、`rejected`
  - `evidence_refs`
    - 约束：非空、去重数组；每项必须是可复验字符串引用
  - `decision`
    - 约束：只允许以下值之一：
      - `approve_shared_capability`
      - `keep_adapter_private`
      - `reject_candidate_capability`
    - 一致性约束：
      - `shared_status=shared` 时只能使用 `approve_shared_capability`
      - `shared_status=adapter_only` 时只能使用 `keep_adapter_private`
      - `shared_status=rejected` 时只能使用 `reject_candidate_capability`
- `ResourceSignal`
  - `signal_key`
    - 约束：非空字符串；表达被观察的资源语义信号名称
  - `signal_role`
    - 约束：只允许 `common_semantic`、`adapter_specific`、`rejected_candidate`
  - `summary`
    - 约束：非空字符串；用一句话表达该信号的语义
  - `source_ref`
    - 约束：非空字符串；指向支持该信号的最小证据引用
- `ApprovedAbstractCapabilityVocabularyEntry`
  - `capability_id`
    - 约束：在 `v0.5.0` 只允许 `managed_account` 或 `managed_proxy`
  - `shared_status`
    - 约束：固定为 `shared`
  - `semantic_boundary`
    - 约束：非空字符串；描述该共享能力在共享层被冻结的边界
  - `non_goals`
    - 约束：非空字符串；描述该能力不应吞入的单平台或技术特定内容

## 生命周期

- 创建：
  - 当 reference adapter 的真实运行差异需要被纳入 `v0.5.0` 资源能力抽象判断时，创建新的 `DualReferenceResourceCapabilityEvidenceRecord`
- 更新：
  - 仅当新增 formal evidence、修正错误分类、或通过正式审查改变 `shared_status / decision` 时，才允许更新该记录
  - 任一更新都不得绕过 `FR-0015` 的有限词汇表与 `shared_status` 枚举约束
- 失效/归档：
  - `FR-0015` 不定义独立归档后端；历史 rejected / adapter-only 记录仍属于正式 evidence truth，不得删除或静默忽略
