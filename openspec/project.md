# Project Context

## Purpose

AI Product Selector is an intelligent workflow automation platform designed for e-commerce product analysis and
selection. The system provides a comprehensive workflow engine that can orchestrate complex AI-driven tasks for product
research, market analysis, and automated decision-making processes.

## Tech Stack

### Backend Framework

- **Python 3.8+** - Primary programming language
- **FastAPI** - Modern, fast web framework for building APIs
- **Uvicorn** - ASGI server for production deployment
- **SQLAlchemy** - Database ORM for data persistence
- **SQLite** - Default database for development and lightweight deployments

### Workflow Orchestration

- **LangGraph** - Core workflow orchestration engine using state graphs
- **LangGraph Checkpoint SQLite** - Workflow state persistence and resumption
- **Pydantic** - Data validation and serialization
- **JSONLogic** - Conditional logic evaluation in workflows

### Web Technologies

- **WebSockets** - Real-time communication for live workflow monitoring
- **Jinja2 Templates** - Server-side HTML templating
- **HTML/CSS/JavaScript** - Frontend user interface
- **Bootstrap** - UI component framework

### Browser Automation

- **Playwright** - Cross-platform browser automation for web scraping
- **Chromium/Firefox/Safari** - Supported browser engines

### Data Processing

- **Pandas** - Data analysis and manipulation
- **OpenPyXL** - Excel file processing
- **Python Multipart** - File upload handling
- **AIOFiles** - Asynchronous file operations

### Development Tools

- **Python-dotenv** - Environment variable management
- **PSUtil** - Process and system monitoring
- **Pytest** - Testing framework (inferred from test files)

## Project Conventions

### 目录规范

### 根目录

```
├── .pytest_cache/       # Pytest cache directory
├── bin/                 # Executable binaries, 服务器的启动脚本、项目的管理脚本，用于启动服务器（测试，开发，生产）
├── docs/                # Documentation files， 主要是人工维护
│   ├── history/         # Historical documentation
│   ├── rpa/             # RPA (Robotic Process Automation) documentation
│   └── specs/           # Specifications documentation
├── openspec/            # OpenSpec configuration and specifications，openspec工具链驱动+人工
│   ├── changes/         # Change proposals and history
│   └── specs/           # Specification files
├── src/                 # Source code directory (currently empty, git-ignored)，老旧代码，不要动
├── src_new/             # New source code directory (primary codebase), 项目主要的源代码
├── tests/               # Test files and test resources, 项目测试的集成测试放在这里
│   └── resources/       # Test resources，测试资源依赖放在这里
 

```

- **禁止** 在src目录里工作，包括改写，新增
- **禁止** 在未被同意的情况下，在根目录下增加文件

### src_new 项目源代码目录

```
├── apps/                    # Application configurations and workflows， 内置的workflow_engine运行的用于验证小程序目录
│   ├── sample_app/          # Example application with multiple workflows，
├── rpa/                     # Robotic Process Automation components
│   └── browser/             # Browser automation utilities
├── workflow_engine/         # Core workflow engine
│   ├── api/                 # FastAPI routes and web server
│   ├── apps/                # App management and loading
│   ├── config/              # Configuration management
│   ├── core/                # Core engine components
│   ├── nodes/               # Node implementations
│   ├── sdk/                 # Software Development Kit for workflow creation
│   ├── storage/             # Database storage components
│   ├── templates/           # HTML templates for UI
│   └── utils/               # Utility functions
├── utils/                   # General utilities
├── builtin_tools/           # 内置的工具, 例如图片相似度工具
└── tests/                   # Test files
```
- **要求** tests/目录的测试文件路径和源代码保持一致，命名为test_xxx.py
- **要求** tests/的输入输出文件要放入到data目录下，避免随意放置

### 编码和设计规范

#### 架构分层原则

- **禁止** 破坏分层规范 - `workflow_engine`和`rpa`之间保持清晰界限，禁止相互耦合
- **禁止** 直接依赖应用层逻辑 - 核心组件不应依赖`apps/`目录下的具体业务实现
- **要求** 使用依赖注入 - 通过`DependencyContainer`管理服务依赖，避免硬编码依赖关系

#### 代码质量原则

- **禁止** 任何形式的硬编码 - 包括文件路径、数据库连接、API端点等，使用配置文件或环境变量
- **要求** 遵循KISS原则 - 优先选择最直接的解决方案，避免过度抽象和复杂设计
- **要求** 遵循SOLID原则 - 模块的设计要符合单一职责、开闭、里氏替换、接口隔离、依赖倒置
- **要求** 类型注解 - 所有公共API和函数签名必须包含完整的类型提示
- **要求** 在新增模块时，应该先分析已有的模块，避免冲突和冗余。

#### 跨平台兼容性

- **要求** 跨平台支持 - 所有代码必须支持macOS、Linux、Windows环境
- **要求** 路径处理规范 - 使用`pathlib.Path`处理文件路径，禁止硬编码路径分隔符
- **要求** 编码统一 - 统一使用UTF-8编码，避免平台相关的编码问题
- **禁止** 平台特定调用 - 避免使用仅在特定操作系统可用的系统调用

#### 异步性能原则

- **要求** 异步优先 - I/O操作（文件、数据库、网络）必须使用`async/await`
- **要求** 非阻塞设计 - FastAPI路由和工作流节点避免同步阻塞操作
- **要求** 连接池管理 - 数据库连接和HTTP客户端使用连接池，避免频繁创建销毁
- **禁止** 混合同步异步 - 在异步上下文中禁止调用同步阻塞函数

#### 资源管理原则

- **要求** 上下文管理器 - 文件、数据库连接、浏览器实例使用`async with`自动释放
- **要求** 内存优化 - 大数据处理使用流式处理，避免一次性加载到内存
- **要求** 浏览器实例管理 - Playwright浏览器实例及时关闭，避免资源泄露
- **要求** 缓存策略 - 对频繁访问的配置和元数据实施合理缓存

#### 并发安全原则

- **要求** 线程安全 - 共享状态访问使用`asyncio.Lock`或线程安全的数据结构
- **要求** 原子操作 - 数据库事务和工作流状态变更保证原子性
- **要求** 状态隔离 - 工作流执行状态在不同运行实例间完全隔离
- **禁止** 全局可变状态 - 避免使用全局变量存储可变状态

#### Python特定规范

- **要求** 异常处理 - 使用具体的异常类型，避免裸露的`except:`语句
- **要求** 生成器优化 - 大数据集处理优先使用生成器和迭代器
- **要求** 装饰器模式 - 使用装饰器实现横切关注点（日志、缓存、重试）
- **要求** 上下文变量 - 使用`contextvars`在异步调用链中传递上下文信息

### Code Style

- **PEP 8** compliance for Python code formatting
- **Type hints** required for all public APIs and function signatures
- **Docstrings** using Google/NumPy style for all classes and functions
- **Snake_case** for variables, functions, and module names
- **PascalCase** for class names
- **UPPER_CASE** for constants and environment variables

### Architecture Patterns

- **Dependency Injection** - Core services managed through DependencyContainer
- **Repository Pattern** - Database operations abstracted through DatabaseManager
- **State Machine Pattern** - Workflows implemented as LangGraph state graphs
- **Modular Router Pattern** - FastAPI routes organized by feature domains
- **Factory Pattern** - Application and workflow creation through managers
- **Observer Pattern** - Real-time logging and monitoring via WebSocket connections

### Testing Strategy

- **Unit Tests** - Individual component testing with pytest
- **Integration Tests** - End-to-end workflow testing
- **API Tests** - simplify-console-tabs- **API Tests** - FastAPI endpoint
  validation，确保所有API端点的功能正确性和数据验证。当有endpoint修改或其依赖代码变更时，必须在编码完成后立即编写相应的单元测试，并确保所有测试通过后才能提交代码。
- **Browser Tests** - 涉及页面的测试优先使用chrome devtool mcp进行测试
- **测试环境** -如果需要开启服务器验证，通过bin/start_server.sh启动服务器进行验证
- **Test Coverage** - Comprehensive coverage for core workflow engine components

## Domain Context

### Workflow Engine Concepts

- **Nodes** - Individual processing units (Python, Condition, Start, End)
- **Edges** - Connections between nodes with optional conditions
- **State** - Workflow execution context with thread-safe data management
- **Signals** - Inter-process communication for pause/resume/cancel operations
- **Checkpoints** - Persistent workflow state for resumption after interruption

### Application Structure

- **Apps** - Self-contained workflow applications with metadata
- **Flows** - Individual workflow definitions within apps
- **Runs** - Workflow execution instances with status tracking
- **Templates** - Reusable HTML templates for workflow consoles

### Business Logic

- **Product Selection** - AI-driven analysis of e-commerce products
- **Market Research** - Automated data collection and analysis
- **Decision Automation** - Rule-based and ML-powered decision making
- **Report Generation** - Automated reporting and data visualization

## Important Constraints

### Technical Constraints

- **Thread Safety** - All database operations must be atomic and thread-safe
- **Cross-Platform** - Must support macOS, Linux, and Windows environments
- **Memory Management** - Efficient handling of large datasets and browser instances
- **Security** - Input validation and sandboxed execution of user-defined code
- **Performance** - Sub-second response times for API endpoints

### Business Constraints

- **Data Privacy** - Secure handling of sensitive product and market data
- **Scalability** - Support for concurrent workflow executions
- **Reliability** - Fault-tolerant execution with automatic retry mechanisms
- **Auditability** - Complete logging and tracing of all workflow operations

### Regulatory Constraints

- **Web Scraping Compliance** - Respect robots.txt and rate limiting
- **Data Retention** - Configurable data lifecycle management
- **Access Control** - Role-based permissions for workflow management

## External Dependencies

### Core Services

- **SQLite Database** - Local data persistence (configurable path: ~/.ren/)
- **File System** - Workflow data, logs, and temporary files
- **Network Services** - HTTP APIs for external data sources

### Browser Infrastructure
- **Playwright MCP** - Study browser behavior and diagnose issues **
- **Playwright Browsers** - Chromium, Firefox, Safari engines
- **System Browsers** - Integration with locally installed browsers
- **Proxy Support** - Optional proxy configuration for network requests

### Development Infrastructure

- **Python Package Index (PyPI)** - Dependency management
- **GitHub** - Source code repository and issue tracking
- **OpenSpec** - Change proposal and specification management

### Runtime Environment

- **Environment Variables** - Configuration through .env files
- **Process Management** - Multi-process workflow execution
- **Log Aggregation** - Centralized logging with configurable outputs






