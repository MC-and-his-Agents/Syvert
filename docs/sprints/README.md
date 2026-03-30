# Syvert Sprint 索引区

本目录用于承载 sprint 级目标、事项聚合、依赖阻塞与 checkpoint 汇总入口。

## 职责边界

- sprint 文档回答“这一轮聚焦哪些事项、依赖和阻塞如何、退出条件是什么”。
- sprint 文档只承载聚合索引，不承载 GitHub backlog 的状态真相。
- sprint 文档通过 `item_key` 关联 `release`、`spec`、`exec-plan` 与 PR。

## 禁止承载的内容

- 不镜像 Project 看板状态。
- 不替代 GitHub iteration / milestone 记录。
- 不复制 formal spec 正文或长任务完整执行日志。

## 模板

- 新 sprint 索引优先从 [./_template.md](./_template.md) 复制。
