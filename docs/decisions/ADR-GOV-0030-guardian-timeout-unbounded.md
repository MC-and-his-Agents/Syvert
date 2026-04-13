# ADR-GOV-0030 Guardian review timeout defaults to unbounded unless configured

## 关联信息

- Issue：`#112`
- item_key：`GOV-0030-guardian-timeout-unbounded`
- item_type：`GOV`
- release：`v0.2.0`
- sprint：`2026-S16`

## 背景

`scripts/pr_guardian.py` 目前把 `SYVERT_GUARDIAN_TIMEOUT_SECONDS` 读取为 `int(os.environ.get(..., "300"))`，这会让 guardian 在未显式配置时仍默认以 300 秒作为超时上限。

guardian 审查经常需要消费较长上下文，且仓库约束已经明确 guardian review 可能达到分钟级甚至更长。如果默认硬编码仍保留 300 秒上限，长时审查会在未显式配置的情况下被中断，破坏 review 与 merge gate 的闭环稳定性。

## 决策

- `GOV-0030` 将 guardian 的默认超时策略调整为“不设置环境变量时不限制超时”。
- `SYVERT_GUARDIAN_TIMEOUT_SECONDS` 仅在显式设置为正整数时生效，并作为 `subprocess.run(timeout=...)` 的秒数传入。
- `SYVERT_GUARDIAN_TIMEOUT_SECONDS` 未设置或为空字符串时表示“不限制超时”；一旦显式设置为 `0`、负数或非整数值，必须立即报错，避免把非法配置静默解释为“关闭超时”。
- 当前事项只修改 guardian 超时策略与对应治理测试，不改变 reviewer rubric、guardian verdict schema、`safe_to_merge` 语义或 merge gate 职责边界。

## 影响

- 未显式配置 guardian 超时时，长时间审查不会再被默认 300 秒上限截断。
- 显式配置超时时，现有运维和调试命令仍可通过环境变量控制上限。
- 后续若要重新引入默认上限，必须通过新的治理事项与 decision 明确说明理由，而不能恢复为隐式硬编码。
