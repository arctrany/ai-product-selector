## 工作流引擎规格文档 - MVP版本

## 一、概述

### 目标
本地可运行、轻量、灵活的流程引擎。核心用 LangGraph 作为编排内核，SQLite 持久化检查点与元数据，提供 API 控制运行（启动、暂停、恢复）。Python 节点以代码仓库内注册函数执行。

### 特点
- 跨平台、无需 Docker（Windows/macOS，Python 3.10+）
- **MVP节点类型**：Python、条件（jsonlogic）
- 节点级暂停/恢复（循环中可编程 interrupt）
- 结构化日志写本地文件并推送控制台
- 版本化与发布（DSL 版本管理）
- 数据库文件存储在 `~/.ren/` 目录

## 二、MVP范围与Backlog

### MVP范围（当前实现）
- **后端服务**：FastAPI + LangGraph + SqliteSaver
- **核心节点**：Python节点（装饰器注册）、条件节点（jsonlogic）
- **控制台功能**：运行状态/日志/暂停恢复API
- **存储系统**：SQLite（~/.ren/）+ 日志滚动
- **暂停/恢复**：节点级中断机制
- **函数注册**：代码装饰器方式，引擎负责依赖安装

### Backlog特性（后续实现）
- **表单节点**：应用层处理，引擎提供API接口
- **React Flow设计器**：可视化流程设计
- **并行节点**：并发执行多分支
- **子流程节点**：调用其他已发布流程
- **HTTP节点**：外部API调用
- **函数版本管理**：签名校验和环境隔离
- **BPMN 2.0支持**：完整语义支持

## 三、技术选型（已确定）

### 核心技术栈
- **编排内核**：LangGraph（StateGraph + SqliteSaver）
- **条件表达式**：jsonlogic（安全、开源）
- **控制API**：FastAPI（REST + WebSocket/SSE）
- **数据存储**：SQLite（~/.ren/workflow.db）
- **日志系统**：本地文件 + 滚动策略
- **函数注册**：Python装饰器

### 业务场景
- **主要流程**：商品数据抓取 → 图片处理 → 相似度计算 → 结果导出
- **运行时长**：4-10小时长流程
- **数据规模**：本地处理10000级别
- **超时策略**：业务自定义（记录日志继续执行或退出）

## 四、架构与组件

- **执行内核**：LangGraph（StateGraph + SqliteSaver）
- **控制 API**：FastAPI（REST + WebSocket/SSE 事件流）
- **状态与元数据**：SQLite 文件（~/.ren/workflow.db）
- **日志**：本地文件（JSON Lines，支持滚动），推送到控制台
- **函数注册**：装饰器系统，白名单管理
- **依赖管理**：引擎负责Python依赖安装

## 五、数据模型（SQLite）

- `flows(id, name, created_at)`
- `flow_versions(id, flow_id, version, dsl_json, compiled_meta, published, created_at)`
- `runs(thread_id, flow_version_id, status, started_at, finished_at, last_event_at, metadata)`
- `signals(id, thread_id, type, payload_json, ts, processed)` 例：pause_request、resume_request
- 检查点表由 SqliteSaver 自动管理

## 六、DSL（JSON格式）

### 节点类型（MVP）
- **type**: `start | end | python | condition`
- **data**: 参数字典
  - **python**: `codeRef/args` - 仓库内注册函数引用
  - **condition**: `expr` - jsonlogic表达式

### 边
- **基本边**：`source/target`
- **条件分支**：`edge.data.when`（jsonlogic表达式结果）

## 七、节点语义

- **Python**：仓库内注册函数（白名单），通过 codeRef 解析并调用；支持循环中的 interrupt
- **条件**：jsonlogic 表达式计算，根据结果走不同边，安全无注入风险

## 八、执行模型与暂停/恢复

### 运行
`graph.invoke/astream`，传入 `thread_id`（configurable），SqliteSaver 持久化状态

### 节点级暂停
- **编程式中断**：节点在安全点调用 `interrupt(value=..., update=...)`
- **外部请求暂停**：API 在 signals 或状态中置 `pause_requested`，节点循环检查到后调用 interrupt

### 恢复
`graph.resume(config, updates)`，从断点继续，支持参数调整

## 九、日志与事件

### 本地文件日志（JSON Lines）
- **格式**：`{"ts": "...", "level": "INFO", "thread_id": "...", "node_id": "...", "message": "...", "context": {...}}`
- **存储**：每线程单独文件 `~/.ren/runs/{thread_id}/logs.jsonl`
- **滚动策略**：按大小（10MB）或按日期轮转

### 控制台推送
后端 tail 线程日志文件，通过 WebSocket/SSE 推送到前端实时展示

### 事件
运行状态变更（start/interrupt/resume/finish/error）写入 signals 并推送

## 十、API 设计（FastAPI）

### 流程与版本
- `POST /flows`
- `POST /flows/{id}/versions`
- `POST /flows/{id}/versions/{ver}/publish`
- `GET /flows/{id}/versions`

### 运行与控制
- `POST /runs/start {flow_id, version, thread_id, input}`
- `GET /runs/{thread_id}`
- `POST /runs/{thread_id}/pause`
- `POST /runs/{thread_id}/resume {updates}`
- `GET /runs/{thread_id}/logs`（分页或下载）
- `WS /runs/{thread_id}/events`（实时日志/事件）

### 控制台功能
- **运行列表**：显示所有运行状态
- **实时日志**：WebSocket推送日志事件
- **暂停/恢复**：手动控制流程执行
- **进度监控**：当前节点和执行进度

## 十一、函数注册系统

### 装饰器注册
```python
from workflow_engine import register_function

@register_function("data.scrape_products")
def scrape_products(state, **kwargs):
    """商品数据抓取"""
    # 实现逻辑
    return {"products": [...]}

@register_function("image.calculate_similarity") 
def calculate_similarity(state, **kwargs):
    """图片相似度计算"""
    # 实现逻辑
    return {"similarity_scores": [...]}
```

### 依赖管理
- 引擎自动检测函数依赖
- 运行时安装缺失的Python包
- 简单隔离策略（同一Python环境）

## 十二、安全与限制

- Python 节点仅运行仓库内注册函数（白名单），避免任意代码执行风险
- 条件表达式使用 jsonlogic，避免代码注入风险
- 文件访问限制在 `~/.ren/` 目录内

## 十三、部署与运行

### 本地运行
```bash
cd src_new
pip install -r requirements.txt
python -m workflow_engine.server --port 8000
```

### 目录结构
```
src_new/
├── workflow_engine/
│   ├── core/           # 核心引擎
│   ├── nodes/          # 节点实现
│   ├── api/            # FastAPI接口
│   ├── storage/        # 存储层
│   └── server.py       # 启动入口
```

### 数据目录
```
~/.ren/
├── workflow.db         # SQLite数据库
├── runs/              # 运行数据
│   └── {thread_id}/
│       ├── logs.jsonl  # 日志文件
│       ├── inputs/     # 输入数据
│       └── outputs/    # 输出结果
```

## 十四、里程碑

- **M1**：核心引擎 + Python/条件节点 + 基础API
- **M2**：控制台功能 + 日志系统 + 暂停恢复
- **M3**：函数注册系统 + 依赖管理
- **M4**：性能优化 + 错误处理 + 文档完善

## 十五、示例工作流

### 商品选品流程
```json
{
  "nodes": [
    {"id": "start", "type": "start"},
    {"id": "scrape", "type": "python", "data": {"codeRef": "data.scrape_products", "args": {"limit": 1000}}},
    {"id": "check_count", "type": "condition", "data": {"expr": {">=": [{"var": "product_count"}, 100]}}},
    {"id": "process_images", "type": "python", "data": {"codeRef": "image.process_batch"}},
    {"id": "calculate_similarity", "type": "python", "data": {"codeRef": "image.calculate_similarity"}},
    {"id": "export_results", "type": "python", "data": {"codeRef": "data.export_excel"}},
    {"id": "end", "type": "end"}
  ],
  "edges": [
    {"source": "start", "target": "scrape"},
    {"source": "scrape", "target": "check_count"},
    {"source": "check_count", "target": "process_images", "data": {"when": true}},
    {"source": "check_count", "target": "end", "data": {"when": false}},
    {"source": "process_images", "target": "calculate_similarity"},
    {"source": "calculate_similarity", "target": "export_results"},
    {"source": "export_results", "target": "end"}
  ]
}
```

---

**实现优先级**：先实现核心引擎和基础节点，确保MVP功能完整可用，后续逐步添加Backlog特性。