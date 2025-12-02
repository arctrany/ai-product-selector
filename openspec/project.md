# 项目上下文

## 项目目标
跨境电商智能选品系统，专注俄语市场OZON平台的自动化数据采集与利润分析。

核心功能：
- 自动抓取OZON商品价格、店铺、跟卖信息
- 实时计算商品利润（含采购成本、佣金、物流）
- 识别优质店铺（≥30%有利润商品）
- Excel批量处理，支持1000+店铺/天

## 技术栈
- Python 3.9+ / asyncio
- Playwright (浏览器自动化)
- openpyxl (Excel处理)
- dataclasses (数据模型)
- pytest (测试)

## 项目约定

### 代码风格
- 类名: PascalCase / 函数: snake_case / 常量: UPPER_SNAKE_CASE
- 必须使用类型注解: `def calculate_profit(price: float) -> float`
- 数据模型用 @dataclass
- 函数 ≤30行，嵌套 ≤3层
- 禁止创建备份文件 (*_backup.py, *_optimized.py, *_fixed.py等)

### 架构模式
- 三层架构: CLI → Common → RPA
- RPA层异步I/O，业务层必须同步（避免async/await）
- 批量处理: 100条/批
- 错误隔离: 单点失败不影响整体

### 模块组织

#### 数据模型 (`common/models/`)
- `business_models.py`: 店铺/商品/价格实体
- `scraping_models.py`: 抓取结果格式
- `enums.py`: 状态枚举
- `exceptions.py`: 自定义异常

#### 配置管理 (`common/config/`)
- `base_config.py`: 基础配置类
- `ozon_selectors_config.py`: OZON选择器
- `seerfar_selectors.py`: Seerfar选择器
- JSON配置文件: 系统参数

#### 工具函数 (`common/utils/`)
- `scraping_utils.py`: 价格提取、文本清理
- `wait_utils.py`: 等待和超时控制
- `model_utils.py`: 数据验证、格式化

#### 业务逻辑 (`common/business/`)
- `pricing_calculator.py`: 价格/佣金/汇率计算
- `profit_evaluator.py`: 利润计算(采购+物流+佣金)
- `store_evaluator.py`: 店铺质量评分

#### 数据抓取 (`common/scrapers/`)
- `ozon_scraper.py`: OZON商品详情抓取
- `seerfar_scraper.py`: Seerfar店铺数据抓取
- `competitor_scraper.py`: 跟卖店铺抓取
- `erp_plugin_scraper.py`: ERP插件数据抓取


**设计原则**: 每个scraper只负责抓取，不做业务计算

#### 浏览器自动化 (`rpa/`)
- `browser_service.py`: 浏览器生命周期管理
- `playwright_browser_driver.py`: Playwright驱动实现
- 支持浏览器实例复用


### 跨平台支持
- 使用 pathlib.Path 处理路径
- UTF-8 编码
- 支持 Windows/macOS/Linux

### 性能优化
- **浏览器复用**: 单例模式，避免重复启动
- **页面限制**: 同时打开 ≤5 个页面
- **超时设置**: 页面加载30s，元素等待10s
- **内存管理**: 分批处理，避免OOM

### 配置策略
- 选择器存储在JSON配置文件
- 优先使用 data-*, id, class 选择器
- 支持俄语/中文/英语关键字

### 测试规范
- **目录结构**: `/tests/` 镜像源代码结构
  - `/tests/unit/` - 单元测试，对应源代码模块
  - `/tests/integration/` - 集成测试
  - `/tests/test_data/` - 测试数据文件
- **命名规则**: test_*.py / Test* / test_*
- **覆盖率**: 核心业务 ≥80%，利润计算 =100%
- **Mock策略**: pytest-mock 模拟外部依赖



## 业务术语
- **OZON平台**: 俄罗斯主要电商平台，类似于Amazon
- **Seerfar**: 第三方数据分析平台，提供店铺销售数据
- **ERP插件**: 浏览器插件，提供商品的采购价格和物流信息
- **跟卖**: 多个卖家销售相同商品的竞争模式
- **利润计算**: 考虑采购价、佣金、物流、汇率等因素的复合计算
- **好店标准**: 基于有利润商品比例判定的店铺质量评估

- **绿标价格**: OZON促销价（绿色标签）
- **黑标价格**: OZON原价（黑色标签）  
- **跟卖**: 多个卖家销售同一商品
- **好店**: ≥30%商品有利润的店铺

## 重要约束
- **平台限制**: 必须遵守OZON等平台的爬虫政策和频率限制
- **浏览器依赖**: 需要Chrome/Chromium、Edge浏览器支持
- **网络稳定性**: 依赖稳定的网络连接进行数据抓取
- **数据准确性**: 价格和库存信息具有时效性
- **跨平台兼容**: 支持Windows、macOS、Linux系统
- **内存使用**: 大批量处理时需要控制内存占用

## 技术实现规范

### 错误处理和重试机制
- **分层异常处理**: 
  - 网络异常: `NetworkError`, `TimeoutError`
  - 页面异常: `PageLoadError`, `ElementNotFoundError`
  - 业务异常: `DataExtractionError`, `ValidationError`
- **智能重试策略**:
  - 网络请求: 指数退避重试，最多3次
  - 页面加载: 线性重试，最多2次
  - 元素查找: 短间隔重试，最多5次
- **优雅降级**: 单个商品/店铺失败不影响整体流程

### 日志和监控规范
- **结构化日志**: 
  - 推荐使用结构化日志格式（支持 JSON 或标准格式）
  - 必须包含时间戳、日志级别、模块名称、消息内容
  - 使用 Python logging 模块，配置统一的日志格式
  - 敏感信息（密码、Token）必须脱敏处理
- **性能监控**: 
  - 记录关键操作的执行时间和资源消耗
  - 对耗时操作（>1秒）输出性能日志
  - 监控内存使用，及时发现内存泄漏
- **错误追踪**: 
  - 详细记录异常堆栈和上下文信息
  - 包含失败时的输入参数和中间状态
  - 使用不同日志级别区分错误严重程度
- **进度报告**: 
  - 实时更新任务进度和状态信息
  - 长时间任务定期输出进度日志（如每处理10%）
  - 提供可视化的进度反馈（CLI 进度条、状态更新）

### 数据验证和清洗
- **输入验证**: 使用Pydantic模型验证所有输入数据
- **数据清洗**: 
  - 价格数据: 去除货币符号，统一数值格式
  - 文本数据: 去除HTML标签，标准化空白字符
  - URL数据: 验证格式，处理相对路径
- **数据完整性**: 确保必要字段不为空，数据类型正确

### 安全和隐私保护
- **用户代理轮换**: 使用多个真实浏览器User-Agent
- **请求频率控制**: 避免过于频繁的请求触发反爬机制
- **数据脱敏**: 敏感信息在日志中进行脱敏处理
- **本地存储**: 避免在代码中硬编码敏感配置信息

## 模块架构

### 📁 CLI模块 (`cli/`) - **分层架构优化**
**职责**: 命令行界面和用户交互层

#### 🎛️ **CLI配置层** (`cli/config/`) - **新增**
**职责**: CLI层专属配置管理
- **`user_config.py`**: CLI用户配置
  - `CLIConfig`: CLI特定配置
  - 用户交互设置和偏好管理

#### 📱 **CLI核心组件**
- **`main.py`**: CLI应用主入口，命令解析和分发
- **`models.py`**: UI数据模型和状态管理
  - `AppState`: 应用状态枚举 (IDLE, RUNNING, PAUSED, COMPLETED, ERROR)
  - `UIConfig`: 用户配置参数 (文件路径、筛选条件、输出设置)
  - `ProgressInfo`: 进度跟踪信息
  - `UIStateManager`: 全局状态管理器，支持事件订阅
- **`task_controller.py`**: 任务控制器，管理任务生命周期
- **`task_control.py`**: **迁移**任务执行控制接口 *(从common迁移)*
- **`preset_manager.py`**: 配置预设管理
- **`log_manager.py`**: 日志管理和导出功能

#### 🔄 **架构分层优化**
- **清晰职责分离**: CLI层只负责用户交互，不处理业务逻辑
- **配置独立管理**: CLI配置与业务配置分离
- **依赖关系优化**: CLI → Common → RPA 的清晰分层

### 📁 Common模块 (`common/`) - **重构后统一模块化架构**
**职责**: 核心业务逻辑和数据处理，采用完全模块化设计

#### 🎯 **数据模型层** (`common/models/`) - **新架构**
**职责**: 统一的数据传输对象和业务实体定义
- **`enums.py`**: 系统枚举定义
  - `ScrapingStatus`: 抓取状态 (SUCCESS, FAILED, PARTIAL, TIMEOUT, ERROR)
  - `FilterType`: 筛选类型
  - `StoreType`: 店铺类型
- **`business_models.py`**: 业务领域模型
  - `StoreInfo`: 店铺基础信息和状态
  - `CompetitorStore`: 跟卖店铺信息
  - `ProductInfo`: 商品信息和价格数据
  - `PriceCalculationResult`: 价格计算结果
- **`scraping_models.py`**: 抓取相关模型
  - `ScrapingResult`: 统一抓取结果格式
  - `CompetitorDetectionResult`: 跟卖检测结果
  - `ProductScrapingResult`: 商品抓取结果扩展
- **`excel_models.py`**: Excel处理模型
  - `ExcelProcessingResult`: Excel处理结果
  - `ExcelValidationError`: Excel验证错误
- **`exceptions.py`**: 自定义异常类
  - `ScrapingException`: 抓取异常基类
  - `ValidationException`: 数据验证异常
- **`__init__.py`**: **向后兼容性导出**
  - 保持原有导入路径的兼容性
  - 统一模型导出接口

#### ⚙️ **配置管理层** (`common/config/`) - **新架构**
**职责**: 分层的配置管理体系
- **`base_config.py`**: 配置基类和主配置
  - `GoodStoreSelectorConfig`: 主系统配置
  - `BaseScrapingConfig`: 抓取配置基类
- **`system_config.py`**: 系统技术配置
  - `LoggingConfig`: 日志系统配置
  - `PerformanceConfig`: 性能配置
- **`business_config.py`**: 业务配置
  - `FilterConfig`: 筛选条件配置
  - `PriceConfig`: 价格计算配置
- **平台选择器配置**:
  - `ozon_selectors_config.py`: OZON选择器配置
  - `seerfar_selectors.py`: Seerfar选择器配置
  - `erp_selectors_config.py`: ERP选择器配置
- **`__init__.py`**: **向后兼容性导出**
  - 保持原有配置导入的兼容性
  - 统一配置接口

#### 🛠️ **工具函数层** (`common/utils/`) - **新架构**
**职责**: 可复用的工具类和辅助函数
- **`model_utils.py`**: **新增**模型相关工具
  - `validate_store_id()`: 店铺ID验证
  - `validate_price()`: 价格数据验证  
  - `format_currency()`: 货币格式化
  - `calculate_profit_rate()`: 利润率计算
- **`scraping_utils.py`**: **增强**抓取工具函数
  - `clean_price_string()`: **迁移**价格字符串清理
  - 统一数据提取和验证功能
  - URL处理和ID提取
- **`wait_utils.py`**: 时序控制工具
- **其他现有工具保持不变**

#### 🔧 业务逻辑子模块 (`common/business/`)
**职责**: 具体的业务逻辑，包括规则计算、价格计算等，提供各种函数可以通过xp_flow注入到各个数据抓取流程中

- **`pricing_calculator.py`**: 价格计算
  - 计算真实的绿标、黑标价格
  - 佣金计算和定价逻辑
  - 汇率转换 (卢布→人民币)
  - 商品定价计算 (95折策略)
  - 完整定价流程和利润分析
- **`profit_evaluator.py`**: 利润评估
  - 通过输入综合的商品信息并利用**利润计算器**，真实的计算利润
  - 考虑采购价、佣金、物流、汇率等因素的复合计算
- **`store_evaluator.py`**: 店铺评估
  - 通过店铺信息以及商品信息，计算店铺的综合评分，用于店铺筛选
  - 基于有利润商品比例判定的店铺质量评估
- **`source_matcher.py`**: 货源匹配器

**架构特点**:
- **规则计算**: 提供各种业务规则的计算函数
- **流程注入**: 通过xp_flow注入到各个数据抓取流程中
- **模块化设计**: 每个业务功能独立封装，便于复用和维护

#### 🕷️ 数据抓取子模块 (`common/scrapers/`)
**职责**: 具体页面的交互过程及抓取，严格按单一职责原则分工

- **`seerfar_scraper.py`**: 只负责seerfar店铺信息的交互和获取，以及seerfar店铺列表商品信息的获取
- **`ozon_scraper.py`**: 只负责商详的信息交互和抓取，不负责逻辑，最后按要求返回商品的详情信息
- **`competitor_scraper.py`**: 只负责跟卖店铺的抓取和交互
- **`erp_plugin_scraper.py`**: 只负责erp插件区域的信息抓取
- **`api_scraper.py`**: 利用api接口获取数据（待建）
- **`xuanping_browser_service.py`**: 选评专用浏览器服务

**设计原则**:
- **单一职责**: 每个scraper只负责特定平台或特定功能的数据抓取
- **职责分离**: 抓取器不负责业务逻辑计算，只负责数据获取和返回
- **标准化接口**: 所有抓取器遵循统一的接口规范

#### 🚨 **向后兼容性保证**
- **`logging_config.py`**: **重新创建**兼容性日志模块
  - 提供原有的 `xuanping_logger`、`setup_logging`、`get_logger` 接口
  - 内部重定向到新的RPA日志系统
  - 保持CLI模块的无缝迁移
- **已废弃的旧文件** (**已安全删除**):
  - ~~`models.py`~~ → 迁移到 `models/` 目录
  - ~~`config.py`~~ → 迁移到 `config/` 目录
  - ~~原 `logging_config.py`~~ → 重新创建兼容版本

#### 📊 其他核心组件
- **`excel_processor.py`**: Excel文件处理 *(保持不变)*
- **`task_control.py`**: 任务控制和状态管理 *(保持不变)*

### 🤖 RPA模块 (`rpa/`)
**职责**: 浏览器自动化和页面操作

#### 核心服务层
- **`browser_service.py`**: 精简版浏览器服务
  - 浏览器生命周期管理
  - 共享实例管理 (支持浏览器复用)
  - 页面导航和组件协调
  - 统一的配置管理和错误处理

#### 接口定义层 (`core/interfaces/`)
- **`browser_driver.py`**: 浏览器驱动抽象接口
- **`page_analyzer.py`**: 页面分析器接口
- **`paginator.py`**: 分页器接口

#### 实现层 (`implementations/`)
- **`playwright_browser_driver.py`**: Playwright浏览器驱动实现
- **`dom_page_analyzer.py`**: DOM页面分析器
- **`universal_paginator.py`**: 通用分页器

#### 配置和模型
- **`core/config/`**: 浏览器服务配置管理
- **`core/models/`**: 页面元素和浏览器状态模型
- **`core/exceptions/`**: 浏览器相关异常定义

#### 架构和编码规范
- **参考文档**: [`rpa/docs/browser_architecture_and_coding_standards.md`](../rpa/docs/browser_architecture_and_coding_standards.md)
  - 定义了浏览器服务模块的架构设计规范
  - 制定了统一的编码标准和最佳实践
  - 包含完整的设计模式、错误处理、跨平台兼容性指南
  - 提供了技术债务清理计划和快速参考指南

### 🧪 Tests模块 (`tests/`)
**职责**: 测试套件和质量保证
- **单元测试**: 各组件的独立功能测试
- **集成测试**: 跨模块协作测试
- **性能测试**: 关键路径性能验证
- **真实场景测试**: 基于实际数据的端到端测试

## 模块依赖关系 - **重构后清晰分层架构**

```
┌─────────────────────────┐
│       CLI Layer         │ ← **应用层** (用户交互)
│   ┌─────────────────┐   │
│   │ CLI Config      │   │ • 命令解析和用户交互
│   │ Task Control    │   │ • 状态管理和进度跟踪
│   │ UI State Mgmt   │   │ • 配置预设管理
│   └─────────────────┘   │
└──────────┬──────────────┘
           │ 依赖 ↓
┌─────────────────────────┐
│      Common Layer       │ ← **核心业务层** (业务逻辑)
│                         │
│ ┌─────────────────────┐ │
│ │    Data Models      │ │ • 统一数据模型和枚举
│ │  Business|Scraping  │ │ • 业务实体和抓取结果
│ │    Excel|Exceptions │ │ • Excel处理和异常定义
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │   Config Manager    │ │ • 分层配置管理
│ │ Base|System|Business│ │ • 系统配置和业务配置
│ │   Platform Configs  │ │ • 平台选择器配置
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │    Utils & Tools    │ │ • 模型工具和抓取工具
│ │  Model|Scraping|Wait│ │ • 时序控制和数据处理
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │  Business Logic     │ │ • 价格计算和利润评估
│ │ Pricing|Profit|Store│ │ • 店铺评估和货源匹配
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │     Scrapers        │ │ • 平台特定的数据抓取
│ │ Seerfar|OZON|ERP    │ │ • 竞争对手和API数据
│ └─────────────────────┘ │
└──────────┬──────────────┘
           │ 依赖 ↓
┌─────────────────────────┐
│        RPA Layer        │ ← **基础设施层** (浏览器自动化)
│                         │
│ ┌─────────────────────┐ │
│ │  Browser Service    │ │ • 浏览器生命周期管理
│ │    Simplified       │ │ • 共享实例和配置管理
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │    Interfaces       │ │ • 抽象接口定义
│ │ Driver|Analyzer|    │ │ • 驱动、分析器、分页器
│ │    Paginator        │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │  Implementations    │ │ • Playwright驱动实现
│ │ Playwright|DOM|     │ │ • DOM分析和通用分页
│ │   Universal         │ │
│ └─────────────────────┘ │
└──────────┬──────────────┘
           │ 通过 ↓
┌─────────────────────────┐
│    External Services    │ ← **外部依赖**
│                         │
│ • OZON平台 (商品数据)    │
│ • Seerfar API (销售数据) │
│ • ERP插件 (采购价格)     │
│ • 1688平台 (货源匹配)    │
│ • 汇率API (实时汇率)     │
└─────────────────────────┘
```

### 🔄 **架构优势**
- **清晰分层**: 应用层 → 业务层 → 基础层 → 外部服务
- **单向依赖**: 高层模块依赖低层模块，避免循环依赖
- **职责分离**: 每层专注特定职责，便于维护和扩展
- **模块化**: 内部模块按功能组织，支持独立开发和测试

### 数据流向
1. **CLI层**: 接收用户输入，管理任务状态
2. **Common层**: 执行核心业务逻辑，协调各个抓取器
3. **RPA层**: 提供浏览器自动化能力，支持页面操作
4. **外部服务**: 提供数据源和业务支持

### 关键设计原则
- **分层架构**: 清晰的职责分离，上层依赖下层
- **接口抽象**: 通过接口定义实现依赖倒置
- **配置驱动**: 通过配置对象管理系统行为
- **异步优先**: 网络IO和文件操作使用异步模式
- **错误隔离**: 单点故障不影响整体系统稳定性
- **避免过度设计**: **MUST** 避免过度设计，无若必要，勿增实体！遵循 YAGNI (You Aren't Gonna Need It) 原则，优先选择简洁明了的实现方案，避免不必要的抽象和复杂性

## 外部依赖
- **OZON网站**: 商品价格和跟卖信息的数据源
- **Seerfar API**: 店铺销售数据和分析报告
- **ERP插件服务**: 商品采购价格和供应链信息
- **1688平台**: 货源匹配和价格对比
- **汇率API**: 实时汇率转换服务
- **浏览器驱动**: ChromeDriver或其他WebDriver实现
