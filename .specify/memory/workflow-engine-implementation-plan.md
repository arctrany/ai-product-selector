# Implementation Plan: Workflow Engine

**Branch**: `main` | **Date**: 2025-10-22 | **Spec**: [specs/workflow_engine.md](../../specs/workflow_engine.md)
**Input**: Feature specification from `specs/workflow_engine.md`

## Summary

本地可运行、轻量、灵活的流程引擎。核心用 LangGraph 作为编排内核，SQLite 持久化检查点与元数据，提供 API 控制运行（启动、暂停、恢复）。Python 节点以代码仓库内注册函数执行。支持商品数据抓取 → 图片处理 → 相似度计算 → 结果导出的业务场景，处理4-10小时长流程和10000级别数据。

## Technical Context

**Language/Version**: Python 3.9+  
**Primary Dependencies**: LangGraph, FastAPI, SQLite, jsonlogic-py  
**Storage**: SQLite (~/.ren/workflow.db)  
**Testing**: pytest (planned for future)  
**Target Platform**: Cross-platform (Windows/macOS), local deployment  
**Project Type**: Independent service with API  
**Performance Goals**: 4-10小时长流程, 10000级别数据处理  
**Constraints**: <10秒启动时间, <100MB内存占用, 本地文件存储  
**Scale/Scope**: 本地单用户, MVP功能集

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **轻量本地优先**: SQLite + 本地文件存储，无需外部依赖  
✅ **安全设计**: 白名单函数注册，jsonlogic安全表达式  
✅ **API优先架构**: FastAPI REST + WebSocket，独立服务  
✅ **弹性执行**: 节点级暂停恢复，长流程支持  
✅ **可扩展函数注册**: 装饰器系统，依赖自动安装

## Project Structure

### Documentation (this feature)

```
.specify/memory/
├── workflow-engine-implementation-plan.md  # This file
├── constitution.md                          # Project constitution
└── domain-knowledge/                       # Domain context

specs/
├── workflow_engine.md                       # Feature specification
└── backlog/                                # Future features
```

### Source Code (repository root)

```
src_new/                                     # Independent workflow engine
├── workflow_engine/                         # Core engine package
│   ├── core/                               # Core components
│   │   ├── models.py                       # Data models
│   │   ├── engine.py                       # LangGraph workflow engine
│   │   └── registry.py                     # Function registration
│   ├── nodes/                              # Node implementations
│   │   ├── base_node.py                    # Base node interface
│   │   ├── python_node.py                  # Python function nodes
│   │   └── condition_node.py               # JSONLogic condition nodes
│   ├── api/                                # FastAPI server
│   │   └── server.py                       # REST API + WebSocket
│   ├── storage/                            # Data persistence
│   │   └── database.py                     # SQLite operations
│   ├── utils/                              # Utilities
│   │   └── logger.py                       # Logging system
│   └── server.py                           # Main entry point
├── examples/                               # Sample workflows
│   ├── sample_functions.py                 # Registered functions
│   └── sample_workflow.py                  # Example workflows
└── requirements.txt                        # Dependencies

~/.ren/                                     # Runtime data directory
├── workflow.db                             # SQLite database
└── runs/                                   # Execution logs
    └── {thread_id}/
        └── logs.jsonl                      # JSON Lines logs
```

**Structure Decision**: Independent service in `src_new/` to avoid conflicts with existing `src/` directory. Runtime data stored in user-agnostic `~/.ren/` directory for cross-platform compatibility.

## Phase 0: Research & Architecture Decisions

### Core Technology Choices

**Decision**: LangGraph + SqliteSaver for workflow orchestration  
**Rationale**: 
- Native Python workflow engine with state management
- Built-in checkpoint persistence for pause/resume
- Mature ecosystem with good documentation
- Lightweight compared to Prefect/Airflow

**Alternatives considered**: Prefect (too heavy), custom state machine (reinventing wheel)

**Decision**: jsonlogic-py for condition expressions  
**Rationale**:
- Safe expression evaluation without code injection
- JSON-based, easy to serialize/store
- Supports complex logical operations
- Fallback implementation for dependency issues

**Alternatives considered**: eval() (unsafe), custom DSL (complex)

**Decision**: FastAPI for REST API + WebSocket  
**Rationale**:
- Modern async Python framework
- Built-in WebSocket support for real-time events
- Automatic OpenAPI documentation
- High performance and easy testing

**Alternatives considered**: Flask (no async), Django (too heavy)

### Storage & Persistence Strategy

**Decision**: SQLite with ~/.ren/ directory  
**Rationale**:
- Cross-platform file-based database
- No external dependencies or setup
- User-agnostic location for system independence
- Supports concurrent access for multi-threading

**Alternatives considered**: JSON files (no ACID), PostgreSQL (external dependency)

### Function Registration & Security

**Decision**: Decorator-based whitelist registration  
**Rationale**:
- Explicit function registration prevents arbitrary code execution
- Simple decorator syntax for developers
- Runtime dependency installation by engine
- Clear separation between engine and business logic

**Alternatives considered**: Dynamic imports (unsafe), plugin system (complex)

## Phase 1: Core Implementation Plan

### 1. Data Models & State Management

**File**: `src_new/workflow_engine/core/models.py`
- WorkflowState: Core state container for LangGraph
- NodeType: Enumeration of supported node types
- RunStatus: Execution status tracking
- Pydantic models for validation and serialization

### 2. Workflow Engine Core

**File**: `src_new/workflow_engine/core/engine.py`
- WorkflowEngine: Main orchestration class
- LangGraph StateGraph integration
- SqliteSaver checkpoint management
- Compile, execute, pause, resume operations

### 3. Node Implementations

**Files**: `src_new/workflow_engine/nodes/`
- BaseNode: Abstract base class for all nodes
- PythonNode: Execute registered functions with interrupt support
- ConditionNode: JSONLogic expression evaluation with fallback

### 4. Function Registry

**File**: `src_new/workflow_engine/core/registry.py`
- @register_function decorator
- Function metadata and signature tracking
- Dependency detection and installation
- Whitelist security enforcement

### 5. Storage Layer

**File**: `src_new/workflow_engine/storage/database.py`
- SQLite schema: flows, flow_versions, flow_runs, signals
- CRUD operations for workflow metadata
- Thread-safe database access
- Migration and initialization

### 6. Logging System

**File**: `src_new/workflow_engine/utils/logger.py`
- JSON Lines format logging
- File rotation and size management
- Real-time log streaming for WebSocket
- Structured logging with context

### 7. API Server

**File**: `src_new/workflow_engine/api/server.py`
- REST endpoints for workflow CRUD and control
- WebSocket for real-time events and logs
- HTML console for monitoring and control
- Error handling and status reporting

## Phase 2: Integration & Testing

### Sample Implementation

**Files**: `src_new/examples/`
- sample_functions.py: Business logic functions for product selection
- sample_workflow.py: Complete workflow definitions
- Integration with core engine for end-to-end testing

### Console Features

- **运行监控**: Real-time workflow status and progress
- **日志查看**: Live log streaming with filtering
- **手动控制**: Pause/resume/stop operations
- **历史记录**: Past execution results and logs

### Dependency Management

- requirements.txt with version constraints
- Fallback implementations for optional dependencies
- Runtime dependency installation for registered functions
- Cross-platform compatibility testing

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Independent service | Avoid conflicts with existing src/ | Integration would require major refactoring |
| LangGraph dependency | Advanced workflow features needed | Custom state machine would be incomplete |
| WebSocket for real-time | Console requires live updates | Polling would be inefficient for long workflows |

## Success Criteria

- ✅ Core engine with LangGraph + SQLite implemented
- ✅ Python and condition nodes working
- ✅ Function registration system operational
- ✅ FastAPI server with REST + WebSocket
- ✅ Console functionality for monitoring
- ✅ File storage and logging system
- 🔄 Integration testing with sample workflows
- ⏳ Performance validation for 10000-item datasets
- ⏳ 4-10 hour long-running workflow testing

## Next Steps

1. **Complete integration testing** with sample workflows
2. **Performance optimization** for large datasets
3. **Error handling improvements** for production readiness
4. **Documentation** for API and function registration
5. **Deployment scripts** for easy setup

---

*Generated by Aone Copilot following spec-kit plan workflow*