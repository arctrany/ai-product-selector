# Spec: 工具类统一管理策略

## Summary

建立统一的工具类管理策略，避免计划中的 `ScrapingUtils` 与现有 `utils/` 目录工具类重复和冲突，通过功能域划分和清晰命名规范，实现工具类的有序管理和高效复用。

## Motivation

### 当前问题
- **工具分散**: 现有 `utils/` 目录包含通用工具，计划的 `ScrapingUtils` 专用于抓取
- **潜在冲突**: 新增工具类可能与现有工具造成命名冲突和功能重叠
- **管理混乱**: 缺乏清晰的工具类组织策略，可能导致重复开发和维护困难

### 预期收益
- **清晰分工**: 按功能域划分工具类，避免职责重叠
- **高效复用**: 统一的工具类管理，提高代码复用率
- **便于维护**: 规范化的工具类结构，降低维护成本

## Detailed Design

### 工具类分层策略

#### 现有工具结构
```
utils/                         # 项目全局通用工具
├── image_similarity.py        # 图像相似度工具
├── result_factory.py          # 结果工厂工具
└── url_converter.py           # URL转换工具
```

#### 目标工具结构
```
utils/                         # 项目全局通用工具（保持不变）
├── image_similarity.py        # 图像相似度工具
├── result_factory.py          # 结果工厂工具
└── url_converter.py           # URL转换工具

common/utils/                  # Scraper专用工具类（新增）
├── __init__.py
├── wait_utils.py              # 时序控制工具
├── scraping_utils.py          # 数据抓取工具
└── selector_utils.py          # 选择器工具
```

### 功能域划分原则

#### 全局工具 (utils/)
- **适用范围**: 整个项目通用，不依赖特定业务逻辑
- **功能特征**: 纯函数式，无状态，高度可复用
- **示例功能**: 图像处理、数据转换、通用算法

#### Scraper专用工具 (common/utils/)
- **适用范围**: 仅限 Scraper 相关功能使用
- **功能特征**: 与抓取业务紧密相关，可能包含状态
- **示例功能**: 页面等待、选择器操作、抓取数据处理

### 核心工具类设计

#### WaitUtils - 时序控制工具
```python
# common/utils/wait_utils.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import Union, Optional

class WaitUtils:
    """页面等待工具类（仅抓取模块使用）"""
    
    @staticmethod
    def wait_for_element(driver, selector: str, timeout: int = 10) -> bool:
        """等待元素出现
        
        Args:
            driver: WebDriver实例
            selector: CSS选择器
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否成功等待到元素
        """
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def wait_for_page_load(driver, timeout: int = 30) -> bool:
        """等待页面加载完成
        
        Args:
            driver: WebDriver实例
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否成功等待页面加载
        """
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except Exception:
            return False
```

#### ScrapingUtils - 数据处理工具
```python
# common/utils/scraping_utils.py
import re
from typing import Optional, Union, List
from selenium.webdriver.remote.webelement import WebElement

class ScrapingUtils:
    """数据抓取工具类（仅抓取模块使用）"""
    
    @staticmethod
    def extract_text_safe(element: Optional[WebElement]) -> str:
        """安全提取元素文本
        
        Args:
            element: 页面元素
            
        Returns:
            str: 提取的文本，失败时返回空字符串
        """
        if element is None:
            return ""
        try:
            return element.text.strip()
        except Exception:
            return ""
    
    @staticmethod
    def parse_price_string(price_text: str) -> Optional[float]:
        """解析价格字符串
        
        Args:
            price_text: 价格文本
            
        Returns:
            Optional[float]: 解析出的价格，失败时返回None
        """
        if not price_text:
            return None
        
        # 移除非数字字符，保留小数点
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        price_clean = price_clean.replace(',', '.')
        
        try:
            return float(price_clean)
        except ValueError:
            return None
    
    @staticmethod
    def extract_number_from_text(text: str) -> Optional[int]:
        """从文本中提取数字
        
        Args:
            text: 包含数字的文本
            
        Returns:
            Optional[int]: 提取的数字，失败时返回None
        """
        if not text:
            return None
        
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        return None
```

#### SelectorUtils - 选择器工具
```python
# common/utils/selector_utils.py
from typing import Optional, Dict, List
import cssselect

class SelectorUtils:
    """选择器工具类（仅抓取模块使用）"""
    
    @staticmethod
    def build_css_selector(category: str, key: str, selectors_map: Dict) -> Optional[str]:
        """构建CSS选择器
        
        Args:
            category: 选择器分类
            key: 选择器键名
            selectors_map: 选择器映射表
            
        Returns:
            Optional[str]: 构建的选择器，失败时返回None
        """
        if category not in selectors_map:
            return None
        
        if key not in selectors_map[category]:
            return None
        
        return selectors_map[category][key]
    
    @staticmethod
    def validate_selector(selector: str) -> bool:
        """验证选择器有效性
        
        Args:
            selector: CSS选择器字符串
            
        Returns:
            bool: 选择器是否有效
        """
        if not selector or not isinstance(selector, str):
            return False
        
        try:
            cssselect.parse(selector)
            return True
        except Exception:
            return False
    
    @staticmethod
    def combine_selectors(selectors: List[str], combinator: str = " ") -> str:
        """组合多个选择器
        
        Args:
            selectors: 选择器列表
            combinator: 组合符（空格、>、+、~ 等）
            
        Returns:
            str: 组合后的选择器
        """
        if not selectors:
            return ""
        
        valid_selectors = [s for s in selectors if s and isinstance(s, str)]
        return combinator.join(valid_selectors)
```

### 命名规范和冲突避免

#### 命名约定
- **全局工具**: `{domain}_{action}.py` (如: `image_similarity.py`)
- **Scraper工具**: `{feature}_utils.py` (如: `wait_utils.py`, `scraping_utils.py`)

#### 命名空间隔离
```python
# common/utils/__init__.py
"""
Scraper工具模块

命名空间隔离策略：
- 所有 Scraper 工具类都在 common.utils 命名空间下
- 与全局 utils 包完全隔离，避免命名冲突
"""

from .wait_utils import WaitUtils
from .scraping_utils import ScrapingUtils  
from .selector_utils import SelectorUtils

__all__ = [
    'WaitUtils',
    'ScrapingUtils',
    'SelectorUtils'
]

# 冲突检测机制
def _check_name_conflicts():
    """检测与全局工具的命名冲突"""
    try:
        import utils as global_utils
        global_names = {name for name in dir(global_utils) if not name.startswith('_')}
        current_names = set(__all__)
        
        conflicts = global_names & current_names
        if conflicts:
            import warnings
            warnings.warn(f"Name conflicts detected with global utils: {conflicts}")
    except ImportError:
        pass

_check_name_conflicts()
```

## Requirements

### ADDED

#### REQ-001: 工具类分层架构
**Status**: ADDED  
**Description**: 建立清晰的工具类分层架构
- 全局工具层：`utils/` 目录，项目通用工具
- Scraper工具层：`common/utils/` 目录，抓取专用工具
- 明确各层职责边界和调用关系

#### REQ-002: Scraper工具目录创建
**Status**: ADDED  
**Description**: 创建 `common/utils/` 目录及基础结构
- 创建 `common/utils/` 目录
- 添加 `__init__.py` 模块初始化文件
- 建立工具类导出接口和命名空间隔离

#### REQ-003: 核心工具类实现
**Status**: ADDED  
**Description**: 实现三个核心 Scraper 工具类
- `WaitUtils`: 时序控制和页面等待工具
- `ScrapingUtils`: 数据提取和处理工具
- `SelectorUtils`: 选择器构建和验证工具

#### REQ-004: 命名冲突检测
**Status**: ADDED  
**Description**: 实现命名冲突检测和预警机制
- 模块加载时自动检测命名冲突
- 冲突发生时发出警告信息
- 提供冲突解决建议和指导

#### REQ-005: 跨平台兼容性
**Status**: ADDED  
**Description**: 确保工具类跨平台兼容性
- Windows、Linux、macOS 平台兼容
- 路径处理的平台适配
- 依赖库的跨平台支持

## Testing Strategy

### 单元测试
- **工具类功能测试**: 每个工具类的核心方法测试
- **边界条件测试**: 异常输入和边界值测试
- **命名冲突测试**: 验证冲突检测机制有效性

### 集成测试
- **工具类协同测试**: 验证不同工具类的协同工作
- **性能基准测试**: 对比工具类使用前后的性能
- **跨平台兼容测试**: 验证在不同操作系统下的表现

### 测试覆盖率目标
- 工具类单元测试覆盖率 ≥ 95%
- 异常处理分支覆盖率 ≥ 90%
- 跨平台兼容性测试覆盖率 = 100%

## Rollout Plan

### 阶段1: 基础架构建设 (2天)
- 创建 `common/utils/` 目录结构
- 实现命名冲突检测机制
- 建立工具类模板和规范

### 阶段2: 核心工具类开发 (3天)
- 实现 `WaitUtils` 时序控制工具
- 实现 `ScrapingUtils` 数据处理工具  
- 实现 `SelectorUtils` 选择器工具

### 阶段3: 集成和迁移 (2天)
- 更新现有代码使用新工具类
- 替换分散的临时工具实现
- 统一工具类使用方式

### 阶段4: 测试和优化 (2天)
- 全面测试工具类功能
- 性能优化和基准测试
- 文档更新和使用指南

### 风险缓解
- **渐进式迁移**: 逐步替换现有工具使用，降低风险
- **向后兼容**: 保持原有接口的兼容性
- **充分测试**: 每个阶段都有完整的测试验证

## Migration Guide

### 使用新工具类

#### 基本导入和使用
```python
# 推荐的导入方式
from common.utils import WaitUtils, ScrapingUtils, SelectorUtils

# 使用示例
def scrape_product_data(driver, selectors_config):
    # 等待页面加载
    if not WaitUtils.wait_for_page_load(driver):
        return None
    
    # 等待价格元素出现
    price_selector = SelectorUtils.build_css_selector(
        'product', 'price', selectors_config.get_selectors_map()
    )
    
    if not WaitUtils.wait_for_element(driver, price_selector):
        return None
    
    # 提取价格数据
    price_element = driver.find_element_by_css_selector(price_selector)
    price_text = ScrapingUtils.extract_text_safe(price_element)
    price_value = ScrapingUtils.parse_price_string(price_text)
    
    return price_value
```

#### 替换现有临时实现
```python
# 替换前：分散的临时实现
def wait_for_element_old(driver, selector):
    time.sleep(5)  # 硬编码等待
    try:
        return driver.find_element_by_css_selector(selector)
    except:
        return None

# 替换后：使用统一工具类
from common.utils import WaitUtils

def wait_for_element_new(driver, selector):
    if WaitUtils.wait_for_element(driver, selector):
        return driver.find_element_by_css_selector(selector)
    return None
```

### 开发规范

#### 新工具类开发模板
```python
# common/utils/new_utils.py
from typing import Optional, Union, List

class NewUtils:
    """新工具类描述
    
    职责：[明确描述工具类职责]
    适用场景：[说明适用的业务场景]
    """
    
    @staticmethod
    def method_name(param: type) -> return_type:
        """方法描述
        
        Args:
            param: 参数描述
            
        Returns:
            return_type: 返回值描述
            
        Raises:
            ExceptionType: 异常描述
        """
        # 实现逻辑
        pass
```

## Metrics

### 成功指标
- ✅ `common/utils/` 目录成功创建
- ✅ 三个核心工具类实现完成
- ✅ 命名冲突检测机制正常工作
- ✅ 所有现有代码成功迁移
- ✅ 零功能回归问题

### 质量指标
- 工具类代码复用率提升 ≥ 40%
- 相关代码重复率降低 ≥ 50%
- 工具类单元测试覆盖率 ≥ 95%
- 工具类调用性能持平或提升

### 监控指标
- 工具类使用频率统计
- 命名冲突事件数量 = 0
- 工具类相关错误日志数量
- 跨平台兼容性问题数量 = 0

### 长期效益评估
- 新功能开发效率提升评估
- 代码维护成本降低评估
- 工具类扩展性和复用性评估
