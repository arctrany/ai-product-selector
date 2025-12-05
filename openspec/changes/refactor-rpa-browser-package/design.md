# 设计文档: RPA 浏览器包重构

## Context

`rpa/` 包是项目的浏览器自动化层，负责与 Playwright 交互、页面分析、分页处理等功能。当前代码存在以下问题：

1. **代码膨胀**: 原 `DOMPageAnalyzer` 从 2397 行精简到 800+ 行，但仍存在冗余
2. **架构过度设计**: 4 层接口继承，但大多数场景只用到核心功能
3. **配置分散**: 配置类散布在多个文件，难以统一管理
4. **异常类过多**: 20+ 个异常类，很多功能重复
5. **目录层次过深**: `core/` 下有 4 层子目录，过于复杂

**依赖方向验证**: ✅ RPA 层不依赖上游代码（common/cli），符合分层架构原则

**约束条件**:
- 必须保持与 `common/scrapers/` 的兼容性（主要使用 `SimplifiedBrowserService`）
- **上层业务层（common/）必须使用同步调用**，RPA 层内部可以是异步但需提供同步封装
- 测试代码可以重新设计，忽略依赖
- 不能影响现有的抓取功能

## Goals / Non-Goals

### Goals
- 精简配置类层次，建立统一配置入口
- 减少异常类数量，采用错误码机制
- 移除所有 print 调试语句，使用标准日志
- 删除未使用的代码和向后兼容别名
- 建立清晰的同步/异步边界
- 提升代码可维护性和可测试性

### Non-Goals
- 不更换 Playwright 为其他浏览器自动化库
- 不改变现有的公开 API 签名（仅内部重构）
- 不增加新的浏览器功能

## Decisions

### Decision 1: 统一配置类层次

**选择**: 合并 `BrowserConfig`、`BrowserServiceConfig`、`PaginatorConfig`、`DOMAnalyzerConfig` 为单一 `UnifiedBrowserConfig`

**当前结构**:
```
BrowserConfig (browser_config.py)
├── ViewportConfig
├── ProxyConfig
├── ExtensionConfig
└── (未使用) PerformanceConfig, SecurityConfig

BrowserServiceConfig (config.py)
├── browser_config: BrowserConfig
├── paginator_config: PaginatorConfig
└── dom_analyzer_config: DOMAnalyzerConfig

ConfigManager (config.py) - 配置管理器
```

**目标结构**:
```
UnifiedBrowserConfig (unified_config.py)
├── browser: BrowserSettings (合并 BrowserConfig 核心字段)
├── viewport: ViewportSettings
├── timeouts: TimeoutSettings
├── pagination: PaginationSettings (简化版)
├── debug: DebugSettings
└── 删除未使用的 PerformanceConfig, SecurityConfig, ExtensionConfig
```

**原因**:
- 减少配置类数量从 8 个到 5 个
- 集中管理，便于验证和序列化
- 删除从未使用的配置类

### Decision 2: 精简异常类层次

**选择**: 保留 5 个核心异常类 + 错误码机制

**当前问题**:
- `TimeoutError` vs `BrowserTimeoutError` - 功能重复
- `ResourceError` vs `ResourceManagementError` - 功能重复
- `PageNavigationError` vs `NavigationError` vs `PageLoadError` - 3 个导航相关异常
- `ElementNotFoundError` vs `ElementNotInteractableError` vs `ElementInteractionError` - 3 个元素相关异常

**目标结构**:
```python
class BrowserError(Exception):
    """统一基类，包含错误码"""
    code: str  # 如 "INIT_FAILED", "TIMEOUT", "ELEMENT_NOT_FOUND"

class InitializationError(BrowserError): pass  # 初始化相关
class NavigationError(BrowserError): pass      # 导航相关
class ElementError(BrowserError): pass         # 元素交互相关
class ResourceError(BrowserError): pass        # 资源管理相关
class AnalysisError(BrowserError): pass        # 页面分析相关
```

**原因**:
- 从 20+ 个减少到 5 个核心异常
- 使用错误码区分具体场景
- 简化异常处理逻辑

### Decision 3: 移除 print 语句，统一日志

**选择**: 全部使用 `StructuredLogger`

**当前问题**:
```python
# universal_paginator.py
print(f"🎯 通用分页器初始化完成")
print(f"   调试模式: {'启用' if debug_mode else '禁用'}")

# browser_detector.py
self.logger.info(f"🔍 发现 {len(profiles)} 个 Profile: {profiles}")
```

混用 print 和 logger，且包含表情符号。

**目标**:
- 移除所有 `print()` 调用
- 统一使用 `self.logger.info/debug/warning/error`
- 日志消息不包含表情符号（除非 debug 模式）

### Decision 4: 简化接口层次（保持同步接口）

**当前结构**:
```
IBrowserDriver (抽象接口)
├── 生命周期管理 (initialize, shutdown)
├── 页面导航 (open_page, get_page_url)
├── 页面操作 (screenshot, execute_script)
├── 元素交互 (wait_for_element, click_element)
├── 会话管理 (verify_login_state, save/load_storage_state)
└── 同步兼容接口 (重复方法)

IPageAnalyzer → IContentExtractor → IElementMatcher → IPageValidator
```

**问题**:
- `IBrowserDriver` 接口过大（30+ 方法）
- 存在重复方法：`screenshot` vs `screenshot_sync`，`get_page_title` vs `get_page_title_sync`
- 4 层分析器接口过度设计

**目标结构**:
```
IBrowserDriver (精简版 - 全部同步接口)
├── 生命周期 (3 方法): initialize(), shutdown(), is_initialized()
├── 导航 (3 方法): open_page(), get_page_url(), get_page_title()
├── 元素 (4 方法): wait_for_element(), click_element(), fill_input(), get_element_text()
└── 页面操作 (2 方法): screenshot(), execute_script()

IAnalyzer (合并 4 个分析器接口 - 同步封装)
```

**关键设计**:
- **对外接口全部同步** - 上层业务层（common/scrapers/）调用同步方法
- **内部实现可异步** - RPA 层内部使用 `asyncio.run()` 或事件循环封装
- 删除 `_sync` 后缀的重复方法，统一为同步接口

### Decision 5: 简化目录结构

**当前结构问题：**
```
rpa/browser/
├── core/
│   ├── config/config.py         # 354行 - 与 models 重复
│   ├── models/browser_config.py # 266行 - 配置模型
│   ├── exceptions/              # 350行 - 20+ 异常
│   └── interfaces/              # 912行 - 4层接口
├── implementations/             # 3470行 - 实现过大
└── utils/                       # 工具类
```

**目标结构：**
```
rpa/browser/
├── config.py              # 合并配置（从 common.BrowserConfig 适配）
├── exceptions.py          # 精简异常（5个核心类）
├── interfaces.py          # 精简接口（合并为 2 个）
├── service.py             # BrowserService（原 browser_service.py）
├── driver/
│   └── playwright.py      # PlaywrightDriver
├── analyzer/
│   └── dom.py             # DOMAnalyzer
├── paginator/
│   └── universal.py       # UniversalPaginator
└── utils/
    ├── detector.py        # 浏览器检测
    └── plugin_checker.py  # 插件检测（新增）
```

**优化点：**
1. 删除 `core/` 层，直接放在 `browser/` 下
2. 合并 `config/` 和 `models/` 为单一 `config.py`
3. 合并 3 个接口文件为 `interfaces.py`
4. 重命名 `implementations/` 为功能明确的子目录
5. 减少目录层次从 4 层到 2 层

### Decision 6: 删除向后兼容别名

**当前问题**:
```python
# dom_page_analyzer.py
OptimizedDOMPageAnalyzer = SimplifiedDOMPageAnalyzer
DOMPageAnalyzer = SimplifiedDOMPageAnalyzer
DOMContentExtractor = SimplifiedDOMPageAnalyzer
DOMElementMatcher = SimplifiedDOMPageAnalyzer
DOMPageValidator = SimplifiedDOMPageAnalyzer

# browser_exceptions.py
ScenarioExecutionError = RunnerExecutionError
```

**选择**: 删除所有别名，统一使用最新类名

**迁移策略**:
1. 在 `__init__.py` 中添加弃用警告
2. 一个版本后删除别名
3. 由于测试可以重新设计，直接更新所有测试代码

## 上游影响分析

### 上游调用方清单

| 模块 | 文件 | 使用方式 | 影响 |
|------|------|----------|------|
| common/scrapers | `__init__.py` | 导出 `SimplifiedBrowserService` | 需更新为 `BrowserService` |
| common/scrapers | `base_scraper.py` | `SimplifiedBrowserService.get_global_instance()` | 需更新类名 |
| common/scrapers | `seerfar_scraper.py` | `SimplifiedBrowserService.get_global_instance()` | 需更新类名 |
| common/scrapers | `ozon_scraper.py` | `SimplifiedBrowserService.get_global_instance()` | 需更新类名 |
| common/scrapers | `competitor_scraper.py` | `SimplifiedBrowserService.get_global_instance()` | 需更新类名 |
| common/scrapers | `erp_plugin_scraper.py` | `SimplifiedBrowserService.get_global_instance()` | 需更新类名 |
| common/services | `scraping_orchestrator.py` | `from rpa... import SimplifiedBrowserService` | 需更新类名 |
| cli | `dependency_checker.py` | 浏览器检测（不使用 RPA） | 无影响 |
| cli | `main.py` | 使用 `config.scraping.browser_type`（已废弃） | 需更新为 `config.browser` |

### 上游使用模式

**模式1: 全局单例获取（主要模式）**
```python
# 所有 scrapers 都使用这种方式
from rpa.browser.browser_service import SimplifiedBrowserService
browser_service = SimplifiedBrowserService.get_global_instance()
```
- 不传递配置，使用默认配置
- 依赖全局单例在其他地方初始化

**模式2: 作为依赖注入（次要模式）**
```python
# scraping_orchestrator.py
def __init__(self, browser_service=None, ...):
    self.browser_service = browser_service
    # 传递给各个 scraper
    self.competitor_scraper = CompetitorScraper(browser_service=self.browser_service)
```
- 可选传入 browser_service
- 但实际调用时通常不传

**模式3: 配置访问（业务层）**
```python
# seerfar_scraper.py
self.base_url = self.config.browser.seerfar_base_url
# ozon_scraper.py
self.base_url = self.config.browser.ozon_base_url
```
- scrapers 使用 `GoodStoreSelectorConfig.browser` 获取业务配置
- 与 RPA 层配置完全分离

### 重构对上游的影响

**需要修改的文件（类名更新）：**
1. `common/scrapers/__init__.py` - 更新导出
2. `common/scrapers/base_scraper.py` - 更新导入
3. `common/scrapers/seerfar_scraper.py` - 更新导入
4. `common/scrapers/ozon_scraper.py` - 更新导入
5. `common/scrapers/competitor_scraper.py` - 更新导入
6. `common/scrapers/erp_plugin_scraper.py` - 更新导入
7. `common/services/scraping_orchestrator.py` - 更新导入
8. `cli/main.py` - 更新 `config.scraping` 为 `config.browser`

**API 兼容性保证：**
- `BrowserService.get_global_instance()` 保持不变
- `browser_service.navigate_to_sync()` 等同步方法保持不变
- `browser_service.get_page_url_sync()` 等方法保持不变

## Risks / Trade-offs

### Risk 1: 破坏现有调用者
**风险**: 类名从 `SimplifiedBrowserService` 改为 `BrowserService`
**缓解措施**:
- 立即更新所有调用方（8个文件）
- 不保留向后兼容别名，直接删除

### Risk 2: 测试覆盖不足
**风险**: 重构后测试可能失效
**缓解措施**:
- 重新设计测试（用户已确认可以忽略依赖）
- 添加集成测试验证核心功能

### Risk 3: 配置传递链路
**风险**: 当前 scrapers 不传递配置给 BrowserService
**缓解措施**:
- 保持 `get_global_instance()` 无参调用支持
- 全局实例使用默认配置，可通过 CLI 初始化时注入

### Trade-off: 简化 vs 灵活性
- **选择**: 优先简化，牺牲部分灵活性
- **权衡**: 当前过度设计的灵活性从未被使用
- **结果**: 代码量减少约 40%，可维护性提升

## Migration Plan

### Phase 1: 配置层重构
1. 创建 `UnifiedBrowserConfig`
2. 添加从旧配置到新配置的转换器
3. 更新 `SimplifiedBrowserService` 使用新配置
4. 删除旧配置类

### Phase 2: 异常层精简
1. 创建精简后的异常类层次
2. 添加错误码常量
3. 更新所有异常抛出点
4. 删除旧异常类

### Phase 3: 日志标准化
1. 移除所有 `print()` 语句
2. 确保所有类都使用 `StructuredLogger`
3. 统一日志格式

### Phase 4: 接口简化和清理
1. 简化 `IBrowserDriver` 接口
2. 合并分析器接口
3. 删除向后兼容别名
4. 删除未使用的代码

### Rollback Plan
- 如果重构导致生产问题，可以 revert 到重构前的提交
- 保留旧代码在单独分支，以备参考

## Open Questions (已解决)

1. **是否保留 `BrowserDetector`?**
   - 当前只用于 Edge 浏览器检测，用于自动选择 Profile
   - **决策**: 保留并扩展，支持 Edge + Chrome 检测，并增加浏览器插件检测功能

2. **分页器是否需要保留所有分页类型?**
   - 当前支持 NUMERIC、LOAD_MORE、INFINITE
   - **决策**: 保留所有分页类型，以支持未来扩展

3. **是否需要保留 Playwright 类型注解?**
   - 当前接口使用 `Optional[Page]`、`Optional[BrowserContext]`
   - 增加了对 Playwright 的紧耦合
   - **决策**: 降低耦合，在接口层使用抽象类型（如 `IPage`、`IBrowserContext`），在实现层适配 Playwright

4. **类命名规范**
   - `SimplifiedBrowserService` 命名不规范
   - **决策**: 重命名为 `BrowserService`，移除 "Simplified" 前缀

5. **单例线程安全**
   - 当前 `SimplifiedBrowserService` 单例缺乏线程安全保护
   - **决策**: 添加线程锁保护单例创建（使用 `threading.Lock`）

6. **向后兼容别名保留时长**
   - 是否保留 `SimplifiedBrowserService = BrowserService` 别名
   - **决策**: 立即删除，不保留向后兼容别名，直接更新所有调用方

7. **插件检测的默认行为**
   - 未安装必需插件时是阻断还是警告
   - **决策**: 可配置，通过 `strict_plugin_check: bool` 控制，默认为 True（阻断）

## 配置系统冗余分析

### 当前问题：两套独立的配置系统

**位置1: common/config/browser_config.py**
```python
@dataclass
class BrowserConfig:
    browser_type: str = "edge"
    headless: bool = False
    window_width: int = 1920
    default_timeout_ms: int = 45000
    seerfar_base_url: str = "https://seerfar.cn"
    ozon_base_url: str = "https://www.ozon.ru"
    # ... 业务相关配置
```
- 被 `GoodStoreSelectorConfig.browser` 使用
- scrapers 通过 `config.browser.xxx` 访问

**位置2: rpa/browser/core/models/browser_config.py**
```python
@dataclass
class BrowserConfig:
    browser_type: BrowserType = BrowserType.PLAYWRIGHT
    headless: bool = False
    viewport: ViewportConfig = field(default_factory=ViewportConfig)
    proxy: Optional[ProxyConfig] = None
    # ... RPA 层配置
```
- 被 `BrowserServiceConfig` 使用
- `SimplifiedBrowserService` 接收 `Dict[str, Any]`

### 配置流向断层
```
用户配置 → common.BrowserConfig → [手动转换] → rpa.BrowserConfig
```

**上游实际使用方式**：
```python
# common/scrapers/seerfar_scraper.py
self.base_url = self.config.browser.seerfar_base_url

# 但 SimplifiedBrowserService 接收的是 Dict
SimplifiedBrowserService.get_global_instance()  # 无法接收 common.BrowserConfig
```

### 决策：收敛配置系统

1. **保留 common/config/browser_config.py 作为唯一业务配置源**
   - 这是用户配置的入口点
   - scrapers 已经在使用

2. **RPA 层接受 common.BrowserConfig 而非 Dict**
   - `BrowserService.__init__(config: Optional[common.BrowserConfig] = None)`
   - 内部转换为 RPA 需要的格式

3. **删除 rpa/browser/core/models/browser_config.py 中的重复定义**
   - 只保留 RPA 特有的配置（如 ViewportConfig）
   - 从 common.BrowserConfig 派生所需值

4. **配置映射层**
   ```python
   # rpa/browser/config_adapter.py
   def adapt_config(common_config: common.BrowserConfig) -> RPAInternalConfig:
       return RPAInternalConfig(
           headless=common_config.headless,
           viewport=ViewportConfig(
               width=common_config.window_width,
               height=common_config.window_height
           ),
           default_timeout=common_config.default_timeout_ms,
           # ...
       )
   ```
