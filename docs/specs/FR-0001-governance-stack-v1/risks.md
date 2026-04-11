# FR-0001 风险记录

## 高风险项

### 1. 状态面漂移

- 风险：guardian、review poller、worktree 状态分散或写入路径不一致，导致判定面失真。
- 缓解：
  - 状态统一到 `$CODEX_HOME/state/syvert/`
  - `governance_status.py` 统一读取并输出状态
  - 对 legacy 状态读取兼容保留测试

### 2. checkpoint 不一致

- 风险：`exec-plan` 与实际 head SHA 或验证结果不一致，导致恢复失败或误判。
- 缓解：
  - `agent-loop` 定义 checkpoint 最小频率与必填字段
  - 每次可验证改动后更新停点、下一步、已验证项、风险、head SHA

### 3. workspace 污染

- 风险：不同事项复用同一目录或错误复用 worktree，导致上下文串扰。
- 缓解：
  - worktree key 固定为 `issue-<number>-<slug>`
  - 创建/复用顺序固定为 `create_worktree.py`
  - branch/worktree/issue 映射入库并可回读

## Stop-Ship 条件

- `WORKFLOW.md` 非法或缺失
- `workflow_guard` 未通过
- guardian 未给出 `APPROVE`
- `safe_to_merge=false`
- GitHub checks 未全绿
- PR `head SHA` 与最新 guardian 审查不一致

## 回滚策略

- 若 v2 引发阻断或误判，通过独立 revert PR 回退本次治理改动。
