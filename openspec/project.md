# 项目上下文

## 项目目标
跨境电商智能选品系统，专注俄语市场OZON平台的自动化数据采集与利润分析。

**核心功能**：
- 自动抓取OZON商品价格、店铺、跟卖信息
- 实时计算商品利润（含采购成本、佣金、物流）
- 识别优质店铺（≥30%有利润商品）
- Excel批量处理，支持1000+店铺/天

## 技术栈
- Python 3.9+ / asyncio
- Playwright (浏览器自动化)
- openpyxl / xlwings (Excel处理)
- dataclasses (数据模型)
- pytest (测试)

## 业务术语
| 术语 | 说明 |
|------|------|
| OZON | 俄罗斯主要电商平台 |
| Seerfar | 第三方数据分析平台，提供店铺销售数据 |
| ERP插件 | 浏览器插件，提供商品采购价格和物流信息 |
| 绿标价格 | OZON促销价（绿色标签） |
| 黑标价格 | OZON原价（黑色标签） |
| 跟卖 | 多个卖家销售同一商品的竞争模式 |
| 好店 | ≥30%商品有利润的店铺 |

---

## 项目约定

### 代码风格
- 类名: PascalCase / 函数: snake_case / 常量: UPPER_SNAKE_CASE
- 必须使用类型注解: `def calculate_profit(price: float) -> float`
- 数据模型用 @dataclass
- 函数 ≤30行，嵌套 ≤3层
- 禁止创建备份文件 (*_backup.py, *_optimized.py 等)

### 架构模式
- **三层架构**: CLI → Common → RPA
- **同步业务层**: RPA层异步I/O，业务层必须同步
- **批量处理**: 100条/批
- **错误隔离**: 单点失败不影响整体

### 跨平台支持
- 使用 pathlib.Path 处理路径
- UTF-8 编码
- 支持 Windows/macOS/Linux

### 性能要求
| 配置项 | 值 |
|--------|-----|
| 浏览器复用 | 单例模式 |
| 同时页面数 | ≤5 |
| 页面加载超时 | 30s |
| 元素等待超时 | 10s |

### 测试规范
- **目录**: `/tests/unit/`, `/tests/integration/`, `/tests/test_data/`
- **命名**: test_*.py / Test* / test_*
- **覆盖率**: 核心业务 ≥80%，利润计算 =100%

---

## 模块架构

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (cli/)                       │
│  用户交互、命令解析、任务控制、状态管理                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ 依赖
┌─────────────────────────▼───────────────────────────────────┐
│                    Common Layer (common/)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │ models/  │ │ config/  │ │ utils/   │ │ excel_engine/    ││
│  │ 数据模型  │ │ 配置管理  │ │ 工具函数  │ │ Excel计算引擎   ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │business/ │ │scrapers/ │ │services/ │ │ excel_processor  ││
│  │ 业务逻辑  │ │ 数据抓取  │ │ 服务编排  │ │ Excel文件处理   ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘│
└─────────────────────────┬───────────────────────────────────┘
                          │ 依赖
┌─────────────────────────▼───────────────────────────────────┐
│                      RPA Layer (rpa/)                        │
│  浏览器自动化、Playwright驱动、页面分析                        │
└─────────────────────────────────────────────────────────────┘
```

### CLI模块 (`cli/`)
| 文件 | 职责 |
|------|------|
| main.py | 应用主入口，命令解析 |
| models.py | UI状态模型 (AppState, UIConfig, ProgressInfo) |
| task_controller.py | 任务生命周期管理 |
| preset_manager.py | 配置预设管理 |

### Common模块 (`common/`)

#### 数据模型 (`models/`)
| 文件 | 内容 |
|------|------|
| business_models.py | StoreInfo, ProductInfo, CompetitorStore |
| scraping_models.py | ScrapingResult, CompetitorDetectionResult |
| excel_models.py | ExcelProcessingResult, ProfitCalculatorInput/Result |
| enums.py | ScrapingStatus, FilterType, StoreType |
| exceptions.py | 自定义异常类 |

#### 配置管理 (`config/`)
| 文件 | 内容 |
|------|------|
| base_config.py | GoodStoreSelectorConfig 主配置 |
| business_config.py | FilterConfig, PriceConfig |
| paths.py | SecurePathConfig 安全路径管理 |
| excel_engine_config.py | 计算引擎配置 |
| *_selectors_config.py | 平台选择器配置 |

#### 业务逻辑 (`business/`)
| 文件 | 职责 |
|------|------|
| pricing_calculator.py | 价格/佣金/汇率计算 |
| profit_evaluator.py | 利润计算（采购+物流+佣金） |
| store_evaluator.py | 店铺质量评分 |
| excel_calculator.py | Excel利润计算器 |

#### 数据抓取 (`scrapers/`)
| 文件 | 职责 |
|------|------|
| ozon_scraper.py | OZON商品详情抓取 |
| seerfar_scraper.py | Seerfar店铺数据抓取 |
| competitor_scraper.py | 跟卖店铺抓取 |
| erp_plugin_scraper.py | ERP插件数据抓取 |

**设计原则**: 每个scraper只负责抓取，不做业务计算

#### Excel计算引擎 (`excel_engine/`)
| 文件 | 职责 |
|------|------|
| base.py | CalculationEngine 协议定义 |
| engine_factory.py | 引擎工厂（自动选择最优引擎） |
| python_engine.py | Python纯计算引擎（跨平台） |
| xlwings_engine.py | Excel自动化引擎（Windows/macOS） |
| compiled_rules.py | 预编译的运费规则（6渠道） |
| validation_engine.py | 跨引擎验证 |

### RPA模块 (`rpa/`)
| 组件 | 职责 |
|------|------|
| browser_service.py | 浏览器生命周期管理 |
| playwright_browser_driver.py | Playwright驱动实现 |
| core/interfaces/ | 抽象接口定义 |
| implementations/ | 具体实现 |

---

## 技术规范

### 错误处理
- **分层异常**: NetworkError, PageLoadError, DataExtractionError
- **重试策略**: 网络请求3次指数退避，页面加载2次
- **优雅降级**: 单个失败不影响整体

### 日志规范
- 使用 Python logging 模块
- 必须包含时间戳、级别、模块名
- 敏感信息必须脱敏
- 耗时操作(>1s)记录性能日志

### 数据验证
- 使用 dataclass 验证输入
- 价格数据去除货币符号，统一格式
- URL验证格式，处理相对路径

### 安全措施
- User-Agent轮换
- 请求频率控制
- 敏感信息脱敏
- 配置文件不硬编码密钥

---

## 外部依赖
| 服务 | 用途 |
|------|------|
| OZON网站 | 商品价格和跟卖信息 |
| Seerfar API | 店铺销售数据 |
| ERP插件 | 采购价格和供应链 |
| 1688平台 | 货源匹配 |
| 汇率API | 实时汇率转换 |

## 重要约束
- 遵守OZON等平台的爬虫政策和频率限制
- 需要Chrome/Chromium、Edge浏览器支持
- 依赖稳定的网络连接
- 价格和库存信息具有时效性
- 大批量处理需控制内存占用

---

## 设计原则
1. **分层架构**: CLI → Common → RPA，单向依赖
2. **接口抽象**: 通过接口实现依赖倒置
3. **配置驱动**: 通过配置对象管理系统行为
4. **错误隔离**: 单点故障不影响整体稳定性
5. **YAGNI**: 避免过度设计，无若必要勿增实体
