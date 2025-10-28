## Why

工作流控制台当前缺少任务执行时间的跟踪功能，用户无法了解任务的实际执行时长。添加计时器功能可以帮助用户：
- 监控任务执行效率
- 评估任务性能
- 进行时间管理和优化

## What Changes

- 在工作流控制台界面添加任务执行时间计时器
- 计时器支持启动、暂停、恢复和停止功能
- 计时器与工作流状态同步，准确记录有效执行时间
- 在界面上实时显示当前执行时间

## Impact

- Affected specs: workflow-console
- Affected code: 
  - 前端控制台界面 (`src_new/workflow_engine/templates/flow_console.html`)
  - 工作流引擎状态管理 (`src_new/workflow_engine/core/engine.py`)
  - WebSocket状态推送机制 (`src_new/workflow_engine/api/workflow_ws.py`)