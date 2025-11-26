# 核心架构重构技术设计

## Context

AI选品系统当前存在4个关键架构问题需要系统性重构：
- 并发浏览器实例导致资源浪费和稳定性问题
- UIConfig和GoodStoreSelectorConfig配置重复造成维护困难
- TaskManager暂停机制不完整，只更新状态未实际控制任务
- GoodStoreSelector绕过ScrapingOrchestrator直接调用scrapers违反架构原则

这些问题影响系统稳定性、可维护性和扩展性，需要进行破坏性架构重构。

## Goals / Non-Goals

### Goals
- 强制使用单一浏览器实例，消除并发浏览器问题
- 统一配置管理，消除重复配置字段
- 实现完整的任务控制机制，支持真正的暂停/恢复
- 强制架构合规，禁止绕过协调器直接调用scrapers
- 保持向后兼容的配置迁移路径
- 提高系统稳定性和可维护性

### Non-Goals
- 不改变核心业务逻辑和算法
- 不引入新的外部依赖
- 不改变用户界面和CLI命令结构
- 不影响现有的数据格式和输出结果

## Decisions

### Decision 1: 强制单一浏览器实例使用
**决策**: 确保所有组件使用现有的全局浏览器单例，禁止创建新的浏览器实例
**理由**: 
- 利用现有的global_browser_singleton.py实现
- 减少资源消耗和避免实例冲突
- 确保系统稳定性和一致性
- 简化浏览器生命周期管理

**实现方案**:
```python
# 确保所有scraper使用全局浏览器单例
from common.scrapers.global_browser_singleton import get_global_browser_service

class BaseScraper:
    def __init__(self, config=None):
        # 强制使用全局浏览器单例
        self.browser_service = get_global_browser_service(config)
        # 移除任何直接的浏览器实例创建

# 在所有scraper子类中确保使用父类的浏览器服务
class OzonScraper(BaseScraper):
    def __init__(self, config=None):
        super().__init__(config)
        # 不创建独立的浏览器实例

class SeerfarScraper(BaseScraper):
    def __init__(self, config=None):
        super().__init__(config)
        # 不创建独立的浏览器实例
```

**验证机制**:
```python
# 添加浏览器实例验证
def verify_single_browser_instance():
    """验证系统中只有一个浏览器实例"""
    import psutil
    browser_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        if 'chrome' in proc.info['name'].lower() or 'edge' in proc.info['name'].lower():
            browser_processes.append(proc)
    
    # 确保只有一个相关的浏览器进程
    assert len(browser_processes) <= 1, f"发现多个浏览器进程: {browser_processes}"
```

**替代方案考虑**: 
- 修改底层架构：不必要，现有单例实现已足够
- 浏览器池模式：增加复杂性，与目标不符

### Decision 2: 配置传递逻辑优化
**决策**: 优化TaskControllerAdapter配置传递，明确配置职责边界
**理由**:
- UIConfig和GoodStoreSelectorConfig职责不同，不应强制统一
- UIConfig处理用户输入参数，GoodStoreSelectorConfig处理系统技术配置
- TaskControllerAdapter只应传递系统级配置，不传递用户业务参数
- 消除语义重复的字段，简化配置维护

**配置职责重新定义**:
```python
from dataclasses import dataclass
from typing import Optional

# UIConfig: 用户输入配置 (通过 --data, --config 传入)
@dataclass  
class UIConfig:
    # 用户业务参数
    margin: float = 0.1
    max_products_per_store: int = 50  # 用户指定的每店商品数
    item_shelf_days: int = 150
    # 文件路径
    good_shop_file: str = ""
    margin_calculator: str = ""
    # 系统级参数
    dryrun: bool = False

# GoodStoreSelectorConfig: 系统技术配置
from common.config.business_config import SelectorFilterConfig
from common.config.base_config import GoodStoreSelectorConfig

class GoodStoreSelectorConfig:
    selector_filter: SelectorFilterConfig
    # 其中 max_products_to_check: int = 10  # 系统默认检查数量
```

**TaskControllerAdapter优化方案**:
```python
from cli.models import UIConfig
from common.config.base_config import GoodStoreSelectorConfig
from good_store_selector import GoodStoreSelector
from typing import Optional

class TaskControllerAdapter:
    def start_task(self, config: UIConfig) -> bool:
        def task_function():
            # 只创建系统配置，传递必要的系统级参数
            selector_config = GoodStoreSelectorConfig()
            selector_config.dryrun = config.dryrun  # ✅ 系统级参数
            
            # 不传递用户业务参数到系统配置
            # ❌ selector_config.selector_filter.max_products_to_check = config.max_products_per_store
            
            # TaskManager配置传递（如果存在）
            task_config = None
            if hasattr(self.task_manager, 'config'):
                task_config = self.task_manager.config
            
            selector = GoodStoreSelector(
                excel_file_path=config.good_shop_file,
                profit_calculator_path=config.margin_calculator,
                config=selector_config,
                task_config=task_config  # 传递TaskManager配置
            )
```

**语义重复字段处理**:
- `UIConfig.max_products_per_store`：用户指定的业务参数，通过业务逻辑传递
- `GoodStoreSelectorConfig.selector_filter.max_products_to_check`：系统技术参数，保持独立
- 不强制统一，保持各自职责边界清晰

**替代方案考虑**:
- 创建统一ApplicationConfig：职责混乱，违反单一职责原则
- 强制参数转换映射：增加不必要的复杂性

### Decision 3: 任务控制机制重构
**决策**: 实现TaskExecutionContext进行任务控制信号传递
**理由**:
- 实现真正的任务暂停，而非仅状态更新
- 提供任务执行者与TaskManager的通信机制
- 支持实时进度报告和状态同步
- 保持任务控制的原子性和一致性

**实现方案**:
```python
import threading
import time
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from task_manager.controllers import TaskManager

class TaskExecutionContext:
    """任务执行上下文，提供任务控制和进度报告"""
    
    def __init__(self, task_id: str, task_manager: 'TaskManager'):
        self.task_id = task_id
        self.task_manager = task_manager
        self._should_stop = threading.Event()
        self._should_pause = threading.Event()
        
    def check_control_point(self, step_name: str = "") -> bool:
        """检查任务控制点"""
        # 检查停止信号
        if self._should_stop.is_set():
            return False
            
        # 检查暂停信号
        if self._should_pause.is_set():
            self._wait_for_resume()
            
        return True
    
    def _wait_for_resume(self):
        """等待恢复信号"""
        while self._should_pause.is_set() and not self._should_stop.is_set():
            time.sleep(0.1)
    
    def pause(self):
        """设置暂停信号"""
        self._should_pause.set()
        
    def resume(self):
        """清除暂停信号"""
        self._should_pause.clear()
        
    def stop(self):
        """设置停止信号"""
        self._should_stop.set()
        self._should_pause.clear()
    
    def report_progress(self, **kwargs):
        """实时报告进度到TaskManager"""
        task_info = self.task_manager.get_task_info(self.task_id)
        if task_info and hasattr(task_info, 'progress'):
            for key, value in kwargs.items():
                if hasattr(task_info.progress, key):
                    setattr(task_info.progress, key, value)
```

**替代方案考虑**:
- 轮询状态检查：性能开销大，响应延迟高
- 异步信号机制：复杂度高，调试困难

### Decision 4: 强制架构合规
**决策**: GoodStoreSelector必须通过ScrapingOrchestrator调用所有scrapers
**理由**:
- 遵循分层架构原则
- 利用协调器的统一错误处理和重试机制
- 提高代码可维护性和可测试性
- 支持统一的监控和日志记录

**实现方案**:
```python
from typing import Optional, Dict, Any
from common.config.base_config import GoodStoreSelectorConfig

class GoodStoreSelector:
    """选品核心业务逻辑类 - 重构为使用协调器"""
    
    def __init__(self, excel_file_path: str, 
                 profit_calculator_path: str,
                 config: Optional[GoodStoreSelectorConfig] = None,
                 task_context: Optional['TaskExecutionContext'] = None):
        # 移除直接scraper实例化:
        # self.ozon_scraper = OzonScraper()
        # self.seerfar_scraper = SeerfarScraper()
        
        # 使用协调器统一管理scrapers
        from common.services.scraping_orchestrator import ScrapingOrchestrator
        self.orchestrator = ScrapingOrchestrator()
        self.task_context = task_context
        
        # 保留其他必要的组件
        self.excel_file_path = excel_file_path
        self.profit_calculator_path = profit_calculator_path
        self.config = config or GoodStoreSelectorConfig()
    
    def _scrape_product_basics(self, product_info: Dict[str, Any]):
        """通过协调器抓取商品价格"""
        try:
            # 检查任务控制点
            if self.task_context and not self.task_context.check_control_point("抓取商品价格"):
                return
                
            # 使用协调器替代直接scraper调用
            from common.services.scraping_orchestrator import ScrapingMode
            result = self.orchestrator.scrape_with_orchestration(
                mode=ScrapingMode.PRODUCT_INFO,
                url=product_info.get('product_url')
            )
            
            if result and hasattr(result, 'success') and result.success:
                if hasattr(result, 'data'):
                    product_info['green_price'] = result.data.get('green_price')
                    product_info['black_price'] = result.data.get('black_price')
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"抓取商品{product_info.get('product_id', 'unknown')}价格失败: {e}")
```

**替代方案考虑**:
- 保持现状加规范检查：不能根本解决架构违规
- 重构协调器接口：影响现有scraper实现

## Risks / Trade-offs

### 风险1: 浏览器性能影响
- **风险**: 单一浏览器实例可能影响并行处理性能
- **缓解**: 
  - 实现浏览器使用队列机制
  - 优化scraper执行效率
  - 监控性能指标调整策略

### 风险2: 破坏性变更影响
- **风险**: 配置格式变更可能影响现有用户
- **缓解**:
  - 提供配置迁移工具
  - 保持向后兼容一个版本周期
  - 详细的升级文档和示例

### 风险3: 任务控制复杂性
- **风险**: 新的任务控制机制可能引入新bug
- **缓解**:
  - 充分的单元测试和集成测试
  - 分阶段实施和验证
  - 保留原有机制作为fallback

### 风险4: 架构合规性验证
- **风险**: 可能存在遗漏的直接scraper调用
- **缓解**:
  - 静态代码分析检查
  - 运行时架构合规性验证
  - 完整的代码审查流程

## Migration Plan

### Phase 1: 浏览器架构重构 (1-2天)
1. 修改GlobalBrowserSingleton实现强制单例
2. 更新BaseScraper使用新的浏览器管理
3. 移除测试中的并发浏览器用例
4. 验证浏览器资源使用和性能

### Phase 2: 配置系统统一 (2-3天)  
1. 设计ApplicationConfig结构
2. 实现配置转换和映射机制
3. 更新TaskControllerAdapter配置处理
4. 提供配置迁移工具和文档

### Phase 3: 任务控制完善 (2-3天)
1. 实现TaskExecutionContext
2. 修改TaskManager支持真实任务控制
3. 集成GoodStoreSelector与新的任务控制
4. 完善进度报告机制

### Phase 4: 架构合规修复 (1-2天)
1. 重构GoodStoreSelector移除直接scraper调用
2. 实现通过ScrapingOrchestrator的统一接口
3. 添加架构合规性验证机制
4. 更新相关测试用例

### Phase 5: 验证和部署 (1天)
1. 运行完整测试套件
2. 性能基准测试
3. 架构合规性验证
4. 文档更新和发布

### 回滚计划
- 保留原有配置格式支持一个版本周期
- Git分支策略支持快速回滚
- 监控指标支持问题快速发现
- 详细的回滚操作文档

## Open Questions

1. ~~是否需要支持多浏览器实例的配置选项？~~ 
   **决定**: 不支持，强制单实例以简化架构
   
2. ~~配置迁移工具是否需要支持批量处理？~~
   **决定**: 支持，提供CLI工具进行批量配置迁移
   
3. ~~任务控制检查点的频率如何确定？~~
   **决定**: 在每个主要业务步骤前检查，避免性能影响

4. ~~是否需要保留直接scraper调用的兼容接口？~~
   **决定**: 不保留，强制架构合规以避免技术债务
