# CHORE-0425 v1.5 creator media evidence 执行计划

## 关联信息

- item_key：`CHORE-0425-v1-5-creator-media-evidence`
- Issue：`#425`
- item_type：`CHORE`
- release：`v1.5.0`
- sprint：`2026-S25`
- Parent Phase：`#381`
- Parent FR：`#405`
- 关联 spec：`docs/specs/FR-0405-creator-profile-media-asset-read-contract/spec.md`
- predecessor PRs：
  - `#428` (`f66136f9772bea348b7ad48ccc766467bc1569ba`)
  - `#439` (`e2e62f8667784d0b746a6c086f259c5268d8430c`)
  - `#440` (`005329da83fe299ff0996099901999117c4f770d`)
  - `#441` (`508c5a5223d75169f374a7db4c15dd7a825702fd`)
- 关联 PR：待创建
- 状态：`active`
- active 收口事项：`CHORE-0425-v1-5-creator-media-evidence`

## 目标

- 交付 `creator_profile_by_id` 与 `media_asset_fetch_by_ref` 的 sanitized fake/reference evidence artifact。
- 用可回放测试固化 evidence schema、平台泄漏边界与 no-storage fail-closed 边界。
- 证明双参考输入在公共 carrier 上语义一致，并保持 `content_detail_by_url`、`FR-0403`、`FR-0404` 回归基线不变。

## 范围

- 本次纳入：
  - `docs/exec-plans/artifacts/CHORE-0425-v1-5-creator-media-evidence.md`
  - `tests/runtime/test_creator_media_evidence.py`
  - 本 exec-plan
- 本次不纳入：
  - creator/media runtime carrier 本体变更（`#422/#423`）。
  - consumer migration 变更（`#424`）。
  - `#426` closeout、`docs/releases/v1.5.0.md`、`docs/sprints/2026-S25.md`、release tag 或 GitHub Release。
  - raw payload files、source names、本地路径、storage handle、private creator/media fields。

## Evidence 不变量

- artifact 只承载 sanitized alias/ref/hash/test command，不承载 raw payload shape 或 source mapping。
- creator scenarios 覆盖 success A/B、not_found、profile_unavailable、permission_denied、rate_limited、platform_failed、provider_or_network_blocked、parse_failed、credential_invalid、verification_required、signature_or_request_invalid。
- media scenarios 覆盖 image/video、metadata_only、source_ref_preserved、downloaded_bytes metadata/audit、media_unavailable、unsupported_content_type、fetch_policy_denied、permission/rate/platform/provider/parse/credential/verification/signature failures、no-storage boundary。
- baseline regression 必须回指 `tests.runtime.test_cli_http_same_path`、`tests.runtime.test_read_side_collection_evidence`、`tests.runtime.test_comment_collection_evidence`。

## 验证记录

- `python3 -m unittest tests.runtime.test_creator_media_evidence`
  - 结果：通过，3 tests。
- `python3 -m unittest tests.runtime.test_creator_media_evidence tests.runtime.test_runtime tests.runtime.test_task_record tests.runtime.test_platform_leakage`
  - 结果：通过，302 tests。
- `python3 -m unittest tests.runtime.test_read_side_collection_evidence tests.runtime.test_comment_collection_evidence tests.runtime.test_cli_http_same_path`
  - 结果：通过，17 tests。
- `python3 -m unittest discover -s tests -p 'test*.py'`
  - 结果：通过，527 tests。
- `python3 scripts/spec_guard.py --mode ci --all`
  - 结果：通过。
- `python3 scripts/docs_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/workflow_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/version_guard.py --mode ci`
  - 结果：通过。
- `python3 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD`
  - 结果：通过。
- `git diff --check`
  - 结果：通过。

## Review finding 处理记录

- 当前尚无 guardian findings，待 PR 创建并执行 `pr_guardian.py review` 后回填。

## 未决风险

- 若 `pr_guardian.py review` 在本地环境再次出现 subprocess hang，本 Work Item 记录阻断并停止，不绕过受控 merge。
- `#426` closeout 仍待消费本 Work Item 合入后的证据与 gate 结果。

## 回滚方式

- 使用独立 revert PR 回滚本 Work Item 的 evidence artifact、tests 与 exec-plan；不影响 `#422/#423/#424` 已合入 runtime/consumer 代码。

## 最近一次 checkpoint 对应的 head SHA

- `508c5a5223d75169f374a7db4c15dd7a825702fd`
