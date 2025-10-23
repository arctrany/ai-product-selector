# Workflow Engine Constitution

## Core Principles

### I. Lightweight & Local-First
本地可运行、轻量、无外部依赖的工作流引擎。所有数据存储在用户本地目录（~/.ren/），支持跨平台部署（Windows/macOS），无需Docker或云服务。引擎必须能够在资源受限环境下稳定运行，启动时间 < 10秒，内存占用 < 100MB。

### II. Security by Design
安全是核心设计原则，不是后加功能。Python节点仅执行仓库内注册的白名单函数，禁止任意代码执行。条件表达式使用jsonlogic确保无代码注入风险。所有用户输入必须经过验证和清理。文件访问严格限制在~/.ren/目录内。

### III. API-First Architecture
所有功能必须通过RESTful API暴露，支持编程式控制。API设计遵循RESTful规范，提供完整的CRUD操作。WebSocket/SSE用于实时事件推送。API响应时间 < 100ms，支持并发请求。控制台功能通过API实现，不依赖特定前端框架。

### IV. Resilient Execution
工作流执行必须支持长时间运行（4-10小时）和大数据量处理（10000级别）。提供节点级暂停/恢复机制，支持检查点持久化。业务可自定义超时和错误处理策略。所有状态变更必须记录日志，支持故障恢复和调试。

### V. Extensible Function Registry
采用装饰器模式的函数注册系统，支持仓库内代码动态注册。引擎负责依赖管理和安装，提供简单的环境隔离。函数必须遵循标准签名约定，支持状态传递和中断机制。注册函数必须提供清晰的文档和错误处理。

## Technology Standards

### Core Technology Stack
- **编排内核**: LangGraph (StateGraph + SqliteSaver)
- **Web框架**: FastAPI (REST + WebSocket/SSE)
- **数据存储**: SQLite (~/.ren/workflow.db)
- **条件引擎**: jsonlogic (安全表达式计算)
- **日志系统**: JSON Lines格式，支持滚动和实时推送
- **Python版本**: 3.10+ (支持类型注解和异步特性)

### MVP节点类型
- **Python节点**: 执行仓库内注册函数，支持参数传递和状态更新
- **条件节点**: 使用jsonlogic表达式进行条件判断和分支控制
- **Start/End节点**: 工作流的入口和出口，处理初始化和清理

### Backlog特性
表单节点、React Flow设计器、并行节点、子流程节点、HTTP节点、函数版本管理、签名校验、环境隔离等特性列入后续开发计划，不影响MVP功能完整性。

## Development Workflow

### Implementation Priority
1. **M1**: 核心引擎架构 + Python/条件节点 + 基础API
2. **M2**: 控制台功能 + 日志系统 + 暂停恢复机制
3. **M3**: 函数注册系统 + 依赖管理 + 错误处理
4. **M4**: 性能优化 + 文档完善 + 集成测试

### Code Organization
- **src_new/**: 工作流引擎独立实现目录
- **~/.ren/**: 用户数据和配置存储目录
- **specs/**: 规格文档和设计说明
- 不修改现有src/目录，保持项目结构清晰

### Quality Standards
- 所有API必须提供完整的错误处理和状态码
- 关键路径必须有日志记录，支持问题排查
- 数据库操作必须支持事务和回滚
- 长时间运行的任务必须支持进度监控

## Business Context

### Primary Use Cases
商品数据抓取 → 图片处理 → 相似度计算 → 结果导出的完整业务流程。支持电商选品、数据分析、批量处理等场景。工作流可运行4-10小时，处理10000级别的数据量。

### Integration Strategy
工作流引擎作为独立服务运行，但可共享Web服务端口。支持应用层表单路由，通过流程APP ID进行请求分发。提供标准API接口，便于与现有系统集成。

## Governance

本Constitution是工作流引擎项目的最高指导原则，所有设计决策和代码实现必须符合这些原则。任何偏离Constitution的行为都需要明确的理由和文档记录。

MVP阶段严格按照确定的技术选型实施，Backlog特性的引入需要重新评估对核心原则的影响。安全性和稳定性是不可妥协的底线。

**Version**: 1.0.0 | **Ratified**: 2025-10-22 | **Last Amended**: 2025-10-22