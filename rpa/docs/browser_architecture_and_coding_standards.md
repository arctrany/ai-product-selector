# 浏览器服务模块架构与编码规范

> 本文档定义了 RPA 浏览器服务模块的架构设计规范和编码标准，适用于所有浏览器自动化相关的开发工作。

## 目录
- [一、架构规范](#一架构规范)
- [二、编码规范](#二编码规范)
- [三、技术债务清理计划](#三技术债务清理计划)

---

## 一、架构规范

### 1.1 分层架构规范

#### 接口层（Interface Layer）
**职责**：定义抽象接口，确保实现的可替换性

**规范要求**：
- 所有接口必须继承自 `ABC`（抽象基类）
- 接口方法必须使用 `@abstractmethod` 装饰器
- 接口命名使用 `I` 前缀，如 `IBrowserDriver`
- 接口应聚焦单一职责，避免"上帝接口"

**示例**：
```python
from abc import ABC, abstractmethod

class IBrowserDriver(ABC):
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化浏览器驱动"""
        pass
```

#### 实现层（Implementation Layer）
**职责**：实现具体的浏览器驱动逻辑

**规范要求**：
- 实现类命名应清晰表达技术栈，如 `PlaywrightBrowserDriver`
- 必须实现接口的所有抽象方法
- 实现特定的优化和平台适配逻辑
- 避免在实现层引入过多业务逻辑

**示例**：
```python
class PlaywrightBrowserDriver(IBrowserDriver):
    async def initialize(self) -> bool:
        """Playwright 浏览器驱动的具体初始化逻辑"""
        # 实现细节
        pass
```

#### 服务层（Service Layer）
**职责**：组织和协调各个组件，提供高层业务接口

**规范要求**：
- 服务类命名使用 `Service` 后缀
- 通过依赖注入获取底层组件
- 提供友好的错误处理和日志
- 封装复杂的调用流程

**示例**：
```python
class SimplifiedBrowserService:
    def __init__(self, driver: IBrowserDriver, config: BrowserConfig):
        self.driver = driver
        self.config = config
```

### 1.2 设计模式规范

#### 工厂模式（Factory Pattern）
- **使用场景**：服务实例创建、配置对象创建
- **命名约定**：`create_*` 或 `*_factory`
- **示例**：`create_simplified_browser_service()`

```python
def create_simplified_browser_service(config: BrowserConfig) -> SimplifiedBrowserService:
    """工厂函数：创建浏览器服务实例"""
    driver = PlaywrightBrowserDriver(config)
    return SimplifiedBrowserService(driver, config)
```

#### 策略模式（Strategy Pattern）
- **使用场景**：分页策略、页面分析策略
- **命名约定**：`*Strategy` 接口，`*StrategyImpl` 实现
- **示例**：`IPaginationStrategy`、`SequentialPaginationStrategy`

#### 单例模式（Singleton Pattern）
- **使用场景**：配置管理器、日志管理器
- **实现方式**：使用类级别的缓存或元类
- **注意事项**：需考虑线程安全

#### 装饰器模式（Decorator Pattern）
- **使用场景**：统一错误处理、日志记录、性能监控
- **命名约定**：`handle_*`、`log_*`、`monitor_*`
- **示例**：`@handle_browser_errors`

```python
def handle_browser_errors(operation_name: str):
    """错误处理装饰器"""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except BrowserError:
                raise
            except Exception as e:
                self.logger.error(f"{operation_name} failed: {e}")
                raise BrowserError(f"{operation_name} failed") from e
        return wrapper
    return decorator
```

### 1.3 配置管理规范

#### 配置层次结构
```
BrowserServiceConfig
├── BrowserConfig（浏览器配置）
├── PaginatorConfig（分页器配置）
├── DOMAnalyzerConfig（分析器配置）
└── LoggingConfig（日志配置）
```

#### 配置验证
- 每个配置类必须实现 `validate()` 方法
- 配置加载后立即验证
- 验证失败时抛出 `ConfigValidationError`

```python
@dataclass
class BrowserConfig:
    browser_type: BrowserType
    headless: bool = False
    
    def validate(self) -> None:
        """验证配置有效性"""
        if not isinstance(self.browser_type, BrowserType):
            raise ConfigValidationError("Invalid browser type")
```

#### 配置来源优先级
1. **环境变量**（最高优先级）
2. **配置文件**（`config.json`）
3. **代码中的默认值**（最低优先级）

```python
class BrowserConfig:
    @classmethod
    def from_env(cls) -> 'BrowserConfig':
        """从环境变量加载配置"""
        return cls(
            browser_type=BrowserType(os.getenv('BROWSER_TYPE', 'chrome')),
            headless=bool(os.getenv('HEADLESS', False)),
        )
```

### 1.4 异步处理规范

#### 异步方法设计
- 核心 I/O 操作必须使用异步方法
- 方法命名不需要 `async_` 前缀（类型注解已表明）
- 支持异步上下文管理器（`__aenter__`、`__aexit__`）

```python
class SimplifiedBrowserService:
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()
```

#### 事件循环管理
- 不要在异步方法中创建新的事件循环
- 使用 `asyncio.create_task()` 创建并发任务
- 在 `shutdown()` 方法中正确清理异步资源

```python
async def shutdown(self):
    """安全关闭浏览器"""
    try:
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    except Exception as e:
        self.logger.error(f"Shutdown error: {e}")
```

#### 超时控制
- 所有异步操作必须设置合理的超时
- 超时时间应可配置
- 超时异常应明确区分类型

```python
async def navigate_to(self, url: str, timeout: int = 30000) -> bool:
    """
    导航到指定URL
    
    Args:
        url: 目标URL
        timeout: 超时时间（毫秒），默认30秒
    """
    try:
        await self.page.goto(url, timeout=timeout)
        return True
    except TimeoutError:
        self.logger.error(f"Navigation timeout: {url}")
        return False
```

### 1.5 错误处理规范

#### 异常层次结构
```python
BrowserError（基类）
├── BrowserInitializationError    # 初始化失败
├── BrowserConnectionError        # 连接失败
├── PageLoadError                 # 页面加载失败
├── ElementNotFoundError          # 元素未找到
└── ConfigValidationError         # 配置验证失败
```

#### 重试机制
- **网络相关操作**：默认重试 3 次
- **使用指数退避策略**
- **可配置最大重试次数和退避系数**

```python
@retry(max_attempts=3, backoff_factor=2.0)
async def fetch_with_retry(self, url: str) -> str:
    """带重试的数据获取"""
    try:
        response = await self.client.get(url)
        return response.text
    except NetworkError as e:
        self.logger.warning(f"Network error: {e}, retrying...")
        raise  # 由装饰器处理重试
```

#### 日志记录
- 错误日志必须包含上下文信息
- 使用结构化日志格式
- 敏感信息（如密码、Token）不得记录

```python
self.logger.error(
    "Failed to load page",
    extra={
        'url': url,
        'error_type': type(e).__name__,
        'context': {'browser': self.browser_type}
    }
)
```

### 1.6 跨平台规范

#### 路径处理
- **必须使用 `pathlib.Path`** 而非字符串拼接
- 使用 `Path.home()` 获取用户目录
- 使用 `os.path.expanduser()` 扩展 `~`

```python
from pathlib import Path

def get_user_data_dir(browser_type: str) -> Path:
    """获取浏览器用户数据目录"""
    system = platform.system().lower()
    if system == "darwin":  # macOS
        if browser_type == 'edge':
            return Path.home() / "Library/Application Support/Microsoft Edge"
        else:
            return Path.home() / "Library/Application Support/Google/Chrome"
    elif system == "windows":
        if browser_type == 'edge':
            return Path.home() / "AppData/Local/Microsoft/Edge/User Data"
        else:
            return Path.home() / "AppData/Local/Google/Chrome/User Data"
    elif system == "linux":
        if browser_type == 'edge':
            return Path.home() / ".config/microsoft-edge"
        else:
            return Path.home() / ".config/google-chrome"
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")
```

#### 平台检测
- 使用 `platform.system()` 检测操作系统
- 支持的平台：**Windows、Linux、macOS**
- 不支持的平台应抛出 `NotImplementedError`

#### 浏览器路径适配
- 各平台默认浏览器路径应通过配置管理
- 支持用户自定义浏览器路径
- 路径不存在时应有明确提示

---

## 二、编码规范

### 2.1 命名规范

#### 类命名
- 使用大驼峰（PascalCase）
- 接口使用 `I` 前缀：`IBrowserDriver`
- 抽象类使用 `Abstract` 前缀或 `Base` 后缀：`AbstractBrowserDriver`
- 异常类使用 `Error` 后缀：`BrowserInitializationError`

#### 方法/函数命名
- 使用小写加下划线（snake_case）
- 布尔返回值使用 `is_`、`has_`、`can_` 前缀
- 异步方法不需要特殊前缀（类型注解已表明）
- 工厂函数使用 `create_` 前缀

```python
# 正确示例
def is_browser_running(self) -> bool: pass
def has_active_page(self) -> bool: pass
async def navigate_to(self, url: str) -> bool: pass
def create_browser_service() -> SimplifiedBrowserService: pass
```

#### 变量命名
- 使用小写加下划线（snake_case）
- 避免单字符变量名（循环变量除外）
- 常量使用全大写加下划线：`DEFAULT_TIMEOUT`
- 私有变量使用单下划线前缀：`_logger`

```python
# 常量
DEFAULT_TIMEOUT = 30000
MAX_RETRY_COUNT = 3

# 私有变量
class BrowserService:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._config = None
```

### 2.2 注释规范

#### 文档字符串（Docstring）
**必需场景**：
- 公共类
- 公共方法
- 复杂函数

**格式**：Google Style 或 NumPy Style

**内容**：简短描述、参数说明、返回值、异常、示例

```python
async def navigate_to(self, url: str, timeout: int = 30000) -> bool:
    """
    导航到指定URL
    
    Args:
        url: 目标URL地址
        timeout: 超时时间（毫秒），默认30秒
        
    Returns:
        bool: 导航是否成功
        
    Raises:
        PageLoadError: 页面加载失败
        TimeoutError: 导航超时
        
    Example:
        >>> await driver.navigate_to("https://example.com")
        True
    """
    pass
```

#### 行内注释
- 用于解释复杂逻辑，而非重复代码
- 放在代码上方，而非行尾
- 使用中文或英文保持一致

```python
# 正确：解释复杂逻辑
# 检测并修正用户数据目录路径（如果指向Profile子目录）
if user_data_dir.endswith('/Default'):
    actual_user_data_dir = os.path.dirname(user_data_dir)

# 错误：重复代码
i = i + 1  # 增加 i 的值
```

#### TODO 注释
**禁止使用 TODO 注释**
- 需要改进的地方应创建 Issue 或技术债务追踪
- 临时方案应在 PR 中说明并设置跟踪

### 2.3 代码结构规范

#### 文件组织
```
rpa/browser/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── interfaces/          # 接口定义
│   │   ├── browser_driver.py
│   │   ├── page_analyzer.py
│   │   └── paginator.py
│   ├── models/              # 数据模型
│   │   ├── browser_config.py
│   │   └── page_element.py
│   ├── config/              # 配置管理
│   │   └── config.py
│   └── exceptions/          # 异常定义
│       └── browser_exceptions.py
├── implementations/         # 具体实现
│   ├── playwright_browser_driver.py
│   ├── dom_page_analyzer.py
│   └── universal_paginator.py
└── browser_service.py       # 服务入口
```

#### 导入顺序
1. 标准库
2. 第三方库
3. 本地模块

```python
# 标准库
import os
import logging
from pathlib import Path
from typing import Optional, List

# 第三方库
from playwright.async_api import async_playwright
from pydantic import BaseModel

# 本地模块
from rpa.browser.core.interfaces import IBrowserDriver
from rpa.browser.core.exceptions import BrowserError
```

#### 类结构顺序
1. 类文档字符串
2. 类变量
3. `__init__` 方法
4. 魔术方法（`__str__`、`__repr__` 等）
5. 属性（`@property`）
6. 公共方法
7. 私有方法

```python
class BrowserService:
    """浏览器服务类"""
    
    # 类变量
    DEFAULT_TIMEOUT = 30000
    
    def __init__(self, config: BrowserConfig):
        """初始化方法"""
        self.config = config
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"BrowserService({self.config.browser_type})"
    
    @property
    def is_running(self) -> bool:
        """浏览器是否运行中"""
        return self._browser is not None
    
    async def initialize(self) -> bool:
        """公共方法：初始化"""
        pass
    
    def _setup_logger(self) -> None:
        """私有方法：设置日志"""
        pass
```

### 2.4 类型注解规范

#### 必需场景
- **所有公共方法**的参数和返回值
- **复杂的数据结构**
- **配置类的所有字段**

```python
from typing import Optional, List, Dict, Any

# 公共方法必须有类型注解
async def process_elements(
    self,
    elements: List[PageElement],
    config: Optional[BrowserConfig] = None
) -> Dict[str, Any]:
    """处理页面元素"""
    pass

# 配置类必须有类型注解
@dataclass
class BrowserConfig:
    browser_type: BrowserType
    headless: bool = False
    debug_port: Optional[int] = None
```

#### 可选场景
- 私有方法（建议添加）
- 简单的局部变量

### 2.5 错误处理规范

#### 异常捕获原则
- **捕获具体异常**，避免裸 `except`
- **记录异常上下文信息**
- **必要时重新抛出或包装异常**

```python
# 正确：捕获具体异常
try:
    await self.page.goto(url)
except TimeoutError as e:
    self.logger.error(f"Page load timeout: {url}")
    raise PageLoadError(f"Failed to load {url}") from e
except NetworkError as e:
    self.logger.warning(f"Network error: {e}, retrying...")
    raise
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
    raise BrowserError(f"Failed to navigate") from e

# 错误：裸 except
try:
    await self.page.goto(url)
except:  # ❌ 不要这样做
    return False
```

#### 错误恢复模式
```python
@retry(max_attempts=3, backoff_factor=2.0)
async def fetch_with_retry(self, url: str) -> str:
    """带重试的数据获取"""
    try:
        response = await self.client.get(url)
        return response.text
    except NetworkError as e:
        self.logger.warning(f"Network error: {e}, retrying...")
        raise  # 由装饰器处理重试
    except Exception as e:
        self.logger.error(f"Unexpected error: {e}")
        raise BrowserError(f"Failed to fetch {url}") from e
```

### 2.6 测试规范

#### 单元测试
- 测试文件命名：`test_*.py`
- 测试类命名：`Test*`
- 测试方法命名：`test_*`
- 每个公共方法至少一个测试用例

```python
# tests/test_browser_service.py
class TestBrowserService:
    async def test_initialize_success(self):
        """测试浏览器初始化成功"""
        service = SimplifiedBrowserService(config)
        result = await service.initialize()
        assert result is True
    
    async def test_navigate_to_valid_url(self):
        """测试导航到有效URL"""
        service = SimplifiedBrowserService(config)
        await service.initialize()
        result = await service.navigate_to("https://example.com")
        assert result is True
```

#### 集成测试
- 测试真实浏览器交互
- 使用测试配置（独立的用户数据目录）
- 测试后清理资源

```python
class TestBrowserIntegration:
    async def test_full_workflow(self):
        """测试完整工作流程"""
        config = BrowserConfig(
            browser_type=BrowserType.CHROME,
            headless=True,
            user_data_dir=Path("./test_data")
        )
        
        async with SimplifiedBrowserService(config) as service:
            await service.navigate_to("https://example.com")
            elements = await service.extract_elements(".item")
            assert len(elements) > 0
```

#### 测试覆盖率
- **核心模块覆盖率** > 80%
- **关键路径覆盖率** = 100%

---

## 三、技术债务清理计划

### 3.1 立即清理项
1. **删除备份文件**
   - 移除所有 `*_backup.py` 文件
   - 使用版本控制系统管理历史

2. **统一注释风格**
   - 补充缺失的文档字符串
   - 统一使用 Google Style 或 NumPy Style

3. **消除代码重复**
   - 提取公共的错误处理逻辑
   - 创建统一的装饰器和工具函数

### 3.2 短期改进项（1-2周）
1. **完善 Linux 支持**
   - 补充 Linux 平台的路径处理
   - 测试 Linux 环境下的浏览器启动

2. **移除硬编码**
   - 将超时时间移到配置
   - 将路径配置化

3. **增强重试机制**
   - 为网络操作添加重试装饰器
   - 实现指数退避策略

### 3.3 中期优化项（1个月）
1. **性能优化**
   - 实现浏览器实例池
   - 优化页面加载速度

2. **监控和日志**
   - 添加性能监控
   - 完善结构化日志

3. **文档完善**
   - 补充 API 文档
   - 提供使用示例

---

## 附录：快速参考

### 常用命令

```bash
# 运行测试
pytest tests/rpa/

# 检查代码风格
flake8 rpa/browser/

# 生成文档
pdoc --html rpa/browser/

# 查看覆盖率
pytest --cov=rpa/browser tests/
```

### 常见错误及解决方案

| 错误类型 | 原因 | 解决方案 |
|---------|------|---------|
| BrowserInitializationError | 浏览器启动失败 | 检查浏览器路径和权限 |
| PageLoadError | 页面加载超时 | 增加超时时间或检查网络 |
| ElementNotFoundError | 元素未找到 | 检查选择器或等待时间 |
| ConfigValidationError | 配置验证失败 | 检查配置格式和必需字段 |

### 推荐工具

- **代码格式化**: `black`, `autopep8`
- **类型检查**: `mypy`, `pyright`
- **代码检查**: `flake8`, `pylint`
- **测试框架**: `pytest`, `unittest`
- **文档生成**: `pdoc`, `sphinx`

---

**文档版本**: 1.0.0  
**最后更新**: 2025-11-20  
**维护者**: RPA 团队
