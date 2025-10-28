# 修复工作流状态更新Bug

## Why

工作流级别的页面中存在严重的状态更新问题：
1. **状态显示不准确**：即使工作流已经启动，页面仍然显示"当前状态: 等待中"
2. **WebSocket连接问题**：前端WebSocket连接到错误的URL路径，导致无法接收状态更新
3. **状态同步失效**：后端状态更新无法传递到前端，用户无法获得实时反馈
4. **初始状态错误**：页面初始化时显示错误的状态信息

## What Changes

- **修复WebSocket URL路径**：将前端连接从错误的 `/api/runs/{threadId}/events` 修正为正确的 `/api/ws/runs/{threadId}/events`
- **完善状态更新逻辑**：确保工作流启动后立即更新页面状态显示
- **增强状态同步机制**：修复后端到前端的状态推送链路
- **优化初始状态处理**：正确处理页面加载时的状态初始化
- **改进错误处理**：增加WebSocket连接失败时的降级处理机制

## Impact

- affected specs: workflow-console
- affected code: 
  - `src_new/workflow_engine/templates/flow_console.html` - 前端WebSocket连接和状态更新逻辑
  - `src_new/workflow_engine/api/workflow_ws.py` - WebSocket路由和状态推送
  - `src_new/workflow_engine/core/engine.py` - 工作流状态更新机制
- **BREAKING**: 无破坏性变更
- 用户体验显著改善，状态显示准确及时
- 修复关键功能缺陷，确保工作流监控正常工作