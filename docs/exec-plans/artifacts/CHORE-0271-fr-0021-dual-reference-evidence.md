# CHORE-0271 FR-0021 Dual Reference Evidence

本文件记录 `#271 / CHORE-0271` 对 `FR-0021` provider port / native provider 拆分后的双参考回归证据。

本文件不改写 [`docs/specs/FR-0021-adapter-provider-port-boundary/`](../../specs/FR-0021-adapter-provider-port-boundary/) 的 requirement；canonical requirement 仍以 formal spec 为准，runtime truth 仍以 `syvert/adapters/xhs.py`、`syvert/adapters/xhs_provider.py`、`syvert/adapters/douyin.py`、`syvert/adapters/douyin_provider.py` 与 registry / runtime 测试为准。

## evidence scope

| 字段 | 值 |
| --- | --- |
| Work Item | `#271 / CHORE-0271-fr-0021-dual-reference-evidence` |
| Parent FR | `#265 / FR-0021-adapter-provider-port-boundary` |
| Release | `v0.7.0` |
| Sprint | `2026-S20` |
| Runtime baseline | `c707fa8d7468fb4fce398234e4448253b83a8c5a` |
| Reference adapters | `xhs`, `douyin` |
| Public operation | `content_detail_by_url` |
| Adapter-facing capability | `content_detail` |
| Target / mode | `url` / `hybrid` |
| Managed resource boundary | `account`, `proxy` |
| Provider boundary | adapter-owned provider port + native provider only |

## regression source report

`#271` 重新运行当前仓内 real adapter regression source report。该 helper 的 frozen reference adapter surface 仍以 `version="v0.2.0"` 绑定，这是历史 version gate 对双参考适配器的冻结矩阵；本证据在 `v0.7.0` worktree head 上复用该矩阵，证明 `FR-0021` 的 provider port 拆分没有改变已批准行为面。

命令：

```bash
python3.11 - <<'PY'
import json
from syvert.real_adapter_regression import run_real_adapter_regression
from tests.runtime.test_real_adapter_regression import RealAdapterRegressionTests

report = run_real_adapter_regression(
    version="v0.2.0",
    adapters=RealAdapterRegressionTests.hermetic_adapters(),
)
print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
PY
```

结果摘要：

| 字段 | 值 |
| --- | --- |
| `source` | `real_adapter_regression` |
| `verdict` | `pass` |
| `version` | `v0.2.0` |
| `semantic_operation` | `content_detail_by_url` |
| `target_type` | `url` |
| `failures` | `[]` |

## regression matrix

| adapter_key | case_id | evidence_ref | expected_outcome | observed_status | observed_error_category |
| --- | --- | --- | --- | --- | --- |
| `xhs` | `xhs-success` | `regression:xhs:success` | `success` | `success` |  |
| `xhs` | `xhs-invalid-input` | `regression:xhs:invalid-input` | `allowed_failure` | `failed` | `invalid_input` |
| `douyin` | `douyin-success` | `regression:douyin:success` | `success` | `success` |  |
| `douyin` | `douyin-platform` | `regression:douyin:platform` | `allowed_failure` | `failed` | `platform` |

## compatibility assertions

| assertion | evidence |
| --- | --- |
| Core public operation 仍是 `content_detail_by_url` | `run_real_adapter_regression()` source report `semantic_operation=content_detail_by_url` |
| Adapter-facing capability 仍是 `content_detail` | `XhsAdapter.supported_capabilities` / `DouyinAdapter.supported_capabilities` 仍为 `{"content_detail"}`，并由 `tests.runtime.test_real_adapter_regression` 冻结 surface 校验 |
| target / mode 仍是 `url` / `hybrid` | `XhsAdapter` / `DouyinAdapter` public metadata 与 regression payload `target_type=url` 共同证明 |
| 资源边界仍只有 `account` + `proxy` | regression resource seed 对两个 adapter 均只种入 `account` 与 `proxy`，且 `#270` SDK 文档已声明 provider port 不新增资源能力 |
| raw payload 与 normalized result 仍由 Adapter 负责 | `tests.runtime.test_xhs_adapter` 与 `tests.runtime.test_douyin_adapter` 覆盖成功 payload shape；`FR-0021` contract 明确 provider 不返回 Syvert normalized result |
| Core / registry 不暴露 provider 字段 | `tests.runtime.test_registry` 与 `#269` runtime implementation 测试覆盖 registry 输出不得出现 provider 字段 |
| 外部 provider 未接入 | 本证据只运行 native provider 拆分后的仓内 reference adapter；未引入 WebEnvoy、OpenCLI、bb-browser、agent-browser 或 provider selector |

## non-approval boundary

- 本证据不批准搜索结果采集、笔记详情之外的评论采集、账号信息采集、账号发布列表采集、图文/视频/长文发布、通知读取/回复、浏览、点赞、收藏、评论等新增业务能力。
- 本证据不批准外部 provider SDK、Core provider registry、provider selector、provider fallback priority 或 provider resource model。
- 本证据不改变 `FR-0013` / `FR-0014` / `FR-0015` 已冻结的 resource requirement、capability matching 与 evidence baseline。

## reproducible commands

```bash
python3.11 -m unittest tests.runtime.test_real_adapter_regression
python3.11 -m unittest tests.runtime.test_xhs_adapter tests.runtime.test_douyin_adapter
python3.11 -m unittest tests.runtime.test_registry tests.runtime.test_version_gate
python3.11 scripts/spec_guard.py --mode ci --base-ref origin/main --head-ref HEAD
python3.11 scripts/docs_guard.py --mode ci
python3.11 scripts/workflow_guard.py --mode ci
python3.11 scripts/governance_gate.py --mode ci --base-ref origin/main --head-ref HEAD
python3.11 scripts/pr_scope_guard.py --class docs --base-ref origin/main --head-ref HEAD
```
