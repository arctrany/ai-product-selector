# Design: Scraper架构统一重构设计文档

## Context

### 背景与约束
当前 Scraper 系统（OzonScraper、CompetitorScraper、SeerfarScraper）存在严重的架构问题，通过深度代码审查发现：

**技术债务问题**:
- **时序控制不一致**：三个 Scraper 都使用大量硬编码 `time.sleep()` 导致系统不稳定
- **职责边界混乱**：`OzonScraper` 承担过多功能，`SeerfarScraper` 通过调用链间接依赖跟卖逻辑
- **代码重复严重**：数据提取、时序控制、错误处理逻辑在三个 Scraper 中重复实现
- **测试覆盖不均**：**SeerfarScraper 测试覆盖率几乎为 0%**，存在重大质量风险

**业务影响**:
- 跟卖检测失败率高，SeerfarScraper 缺乏测试保障
- 三个 Scraper 的维护成本持续上升，新功能开发困难
- 重复逻辑和时序问题影响整体性能和用户体验
- SeerfarScraper 几乎无测试覆盖，生产环境存在未知风险

**技术约束**:
- 必须保持向后兼容性，但是不要过度冗余，不能破坏现有API调用
- 需要支持跨平台兼容性（Windows, Linux, macOS）
- 遵循项目现有的技术栈和架构模式

## Goals / Non-Goals

### Goals
1. **架构清晰化**: 建立清晰的模块边界和职责分离
2. **时序统一化**: 统一时序控制机制，消除硬编码等待
3. **代码复用化**: 建立统一工具类，消除重复逻辑
4. **接口标准化**: 统一方法签名和数据格式
5. **可维护性**: 降低维护成本，提高新功能开发效率
6. **性能优化**: 提高跟卖检测成功率和响应速度

### Non-Goals
1. **功能变更**: 不改变现有业务功能和用户体验
2. **UI重构**: 不涉及用户界面的变更
3. **数据迁移**: 不涉及历史数据的迁移和转换
4. **第三方集成**: 不新增外部服务依赖

## Decisions

### 决策1: 采用服务分层架构模式
**决策**: 引入分层架构，将跟卖逻辑从抓取器中分离

**理由**:
- 符合单一职责原则，每个组件职责明确
- 提高代码的可测试性和可维护性
- 支持功能的独立扩展和优化

**架构层次**:
```
┌─────────────────────────────────────┐
│           协调层 (Orchestrator)      │  ← 统一入口，业务编排
├─────────────────────────────────────┤
│        服务层 (Services)             │  ← 业务逻辑，跟卖检测
├─────────────────────────────────────┤
│        抓取层 (Scrapers)             │  ← 三个 Scraper 统一架构
│  ┌─────────────────────────────────┐ │
│  │ SeerfarScraper                  │ │  ← Seerfar 平台数据收集
│  │ OzonScraper                     │ │  ← OZON 基础商品信息
│  │ CompetitorScraper               │ │  ← 跟卖店铺数据抓取
│  └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│        工具层 (Utils)                │  ← 统一工具，三个 Scraper 共享
│  WaitUtils | ScrapingUtils          │  ← 时序控制 | 数据提取
├─────────────────────────────────────┤
│        配置层 (Config)               │  ← 统一配置管理
│  BaseScrapingConfig                 │  ← 基础配置类
│  SeerfarSelectors | OzonSelectors   │  ← 继承统一接口
├─────────────────────────────────────┤
│        数据层 (Models)               │  ← 数据模型，标准格式
│  ScrapingResult                     │  ← 统一数据传输格式
└─────────────────────────────────────┘
```

### 决策2: 三个 Scraper 统一时序控制策略
**决策**: 创建 `WaitUtils` 工具类，为 SeerfarScraper、OzonScraper、CompetitorScraper 提供统一时序控制

**理由**:
- 三个 Scraper 都存在硬编码等待问题，需要统一解决
- 显式等待比固定等待更可靠，能根据实际页面状态响应
- 统一时序控制便于维护和调优，支持跨平台兼容性

**技术实现**:
```python
class WaitUtils:
    @staticmethod
    def wait_for_element_visible(page, selector: str, timeout: int = 30):
        """等待元素可见，返回元素对象"""
        pass
    
    @staticmethod  
    def wait_for_url_change(page, original_url: str, timeout: int = 30) -> bool:
        """等待URL变化，返回是否成功"""
        pass
```

**配置化支持**:
- 支持环境变量配置超时时间
- 支持不同操作类型的默认超时设置
- 支持重试机制和降级策略

### 决策3: 建立三个 Scraper 统一数据格式
**决策**: 定义标准的 `ScrapingResult` 数据传输对象，适用于所有 Scraper

**理由**:
- 三个 Scraper 返回格式不一致，需要统一标准
- 统一接口提高系统一致性，降低调用方复杂度
- 标准错误处理和统一格式降低调试和维护成本

**数据结构设计**:
```python
class ScrapingResult:
    def __init__(self, success: bool, data: dict, 
                 error_message: str = None, error_code: str = None, 
                 metadata: dict = None):
        self.success = success                    # 操作是否成功
        self.data = data                         # 核心数据
        self.error_message = error_message       # 错误信息
        self.error_code = error_code             # 错误代码
        self.metadata = metadata or {}           # 元数据
```

### 决策4: 建立统一测试框架（急需补齐 SeerfarScraper 测试）
**决策**: 创建 `BaseScraperTest` 统一测试基类，急需补齐 SeerfarScraper 测试覆盖

**理由**:
- **SeerfarScraper 测试覆盖率几乎为 0%**，存在重大质量风险
- 三个 Scraper 测试代码重复（浏览器初始化、Mock 模式等）
- 统一测试框架提高测试效率和一致性，降低维护成本

**实现方式**:
- 创建 BaseScraperTest 基类，提供统一的测试工具和 Mock 框架
- **紧急为 SeerfarScraper 创建完整测试套件**
- 建立集成测试验证多 Scraper 协同工作

### 决策5: 依赖注入模式实现三个 Scraper 解耦
**决策**: 使用依赖注入减少三个 Scraper 间的直接依赖

**理由**:
- 简化 SeerfarScraper → OzonScraper → CompetitorScraper 复杂调用链
- 降低模块耦合度，提高可测试性
- 支持运行时配置和模块替换

**实现方式**:
- 构造函数注入：主要依赖通过构造函数传入
- 配置注入：通过配置文件控制依赖关系
- 工厂模式：统一创建和管理对象生命周期

### 决策6: 配置层完全统一管理
**决策**: 完善 `BaseSelectorConfig` 基类，确保所有 Selectors 统一继承和管理

**理由**:
- 当前 OzonSelectors 和其他 Selectors 配置管理分散，缺乏统一的继承体系
- 统一配置管理便于维护和扩展，降低配置错误风险
- 建立完整的配置继承体系，支持配置复用和覆盖机制

**技术实现**:
```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

# 完善基类设计
class BaseSelectorConfig(ABC):
    @abstractmethod
    def get_selector(self, category: str, key: str) -> Optional[str]:
        """获取选择器"""
        pass
    
    @abstractmethod  
    def validate_config(self) -> List[str]:
        """验证配置有效性"""
        pass
    
    @abstractmethod
    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        """批量获取选择器"""
        pass

# 确保继承关系
class OzonSelectorsConfig(BaseSelectorConfig):
    def get_selector(self, category: str, key: str) -> Optional[str]:
        # 实现具体的选择器获取逻辑
        return self._selector_map.get(category, {}).get(key)
    
    def validate_config(self) -> List[str]:
        # 实现配置验证逻辑
        errors = []
        if not hasattr(self, '_selector_map'):
            errors.append("Missing selector configuration")
        return errors
    
    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        return self._selector_map.get(category)

class SeerfarSelectorsConfig(BaseSelectorConfig):
    def get_selector(self, category: str, key: str) -> Optional[str]:
        # 实现具体的选择器获取逻辑
        return self._selector_map.get(category, {}).get(key)
    
    def validate_config(self) -> List[str]:
        # 实现配置验证逻辑
        errors = []
        if not hasattr(self, '_selector_map'):
            errors.append("Missing selector configuration")
        return errors
    
    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        return self._selector_map.get(category)
```

**配置管理策略**:
- 建立配置优先级管理（环境变量 > 配置文件 > 默认值）
- 统一配置验证和错误处理机制
- 支持配置热更新和动态加载

### 决策7: 业务层目录重组
**决策**: 将 `filter_manager.py` 从 `common/scrapers/` 移动到项目根目录下的 `business/`

**理由**:
- `filter_manager.py` 包含店铺和商品过滤的业务逻辑，不属于数据抓取层
- 明确业务逻辑和数据抓取的职责边界，符合分层架构原则
- 提高代码组织的逻辑性和可维护性

**目录结构重组**:
```
# 项目根目录结构重组
business/                  # 新增业务层目录（项目根目录下）
├── __init__.py
├── filter_manager.py      # 从 common/scrapers/ 移动过来
├── profit_evaluator.py
└── store_evaluator.py

common/
├── scrapers/              # 纯数据抓取层
│   ├── seerfar_scraper.py
│   ├── ozon_scraper.py
│   └── competitor_scraper.py
└── services/              # 服务层
    └── competitor_detection_service.py
```

**迁移策略**:
- 更新所有导入引用: `from common.scrapers.filter_manager` -> `from business.filter_manager`
- 验证功能完整性，确保移动后所有调用正常
- 更新相关文档和测试用例

### 决策8: 工具类统一管理策略
**决策**: 建立统一的工具类管理策略，避免 ScrapingUtils 与现有 utils/ 工具类重复和冲突

**理由**:
- 现有 `utils/` 目录包含 `image_similarity.py`, `result_factory.py`, `url_converter.py`
- 计划的 `ScrapingUtils` 与现有工具可能造成管理混乱和依赖冲突
- 需要建立清晰的工具类组织结构，避免重复功能和维护困难

**统一策略设计**:
```
utils/                     # 通用工具类（项目全局）
├── image_similarity.py    # 图像相似度工具
├── result_factory.py      # 结果工厂工具
└── url_converter.py       # URL转换工具

common/utils/              # Scraper专用工具类
├── wait_utils.py          # 时序控制工具
├── scraping_utils.py      # 数据抓取工具
└── selector_utils.py      # 选择器工具
```

**避免冲突的原则**:
- 按功能域划分：通用工具 vs Scraper专用工具
- 明确命名规范：避免功能重复和名称冲突
- 建立依赖关系图：防止循环依赖

### 决策9: 架构铁律文档化
**决策**: 将所有架构原则和设计决策更新到 `project.md` 文档中

**理由**:
- 架构原则和设计决策缺乏正式文档化，影响团队一致性
- 新团队成员需要了解项目的架构约束和设计理念
- 确保架构原则得到制度化，便于长期维护和决策参考

**文档化内容**:
```markdown
## 架构铁律

### 分层架构原则
- 协调层：统一入口，业务编排
- 服务层：业务逻辑处理
- 抓取层：数据抓取，页面操作
- 工具层：通用工具，跨模块复用
- 配置层：统一配置管理
- 数据层：数据模型，标准格式

### 职责分离原则
- 每个组件遵循单一职责原则
- 避免跨层直接调用，通过接口交互
- 业务逻辑与数据抓取严格分离

### 技术约束
- 避免硬编码，使用配置化管理
- 跨平台兼容性（Windows, Linux, macOS）
- 能同步处理，就不要异步
- 避免重复代码，建立统一工具类
```

**维护策略**:
- 每次架构变更必须更新 project.md
- 定期审查架构原则的执行情况
- 建立架构决策的追溯机制

## Alternatives Considered

### 备选方案1: 渐进式重构 vs 大规模重构
**考虑的方案**: 分模块逐步重构 vs 一次性架构重构

**选择**: 分阶段重构，先建立基础设施再逐步迁移

**理由**:
- 降低风险，每个阶段都可独立验证
- 保持系统稳定，不影响线上服务
- 团队可以逐步适应新架构

### 备选方案2: 同步 vs 异步架构 -> 同步优先
**考虑的方案**: 保持同步架构 vs 引入异步处理

**选择**: 保持同步架构，符合项目原则"能同步处理，就不要异步"

**理由**:
- 符合项目技术规范要求
- 降低复杂度，便于调试和维护
- 当前业务场景不需要高并发处理

### 备选方案3: 自研工具类 vs 第三方库  
**考虑的方案**: 自行实现工具类 vs 引入第三方等待库

**选择**: 用第三方库

## Risks / Trade-offs

### 风险1: 重构引入新Bug -> 通过严格的单元测试
**风险描述**: 大规模代码重构可能引入新的缺陷
**风险等级**: 中等
**缓解措施**:
- 全面的单元测试覆盖（目标95%+）
- 分阶段实施，每阶段充分验证
- 保持现有测试用例通过
- 建立回滚机制

### 风险2: 向后兼容性破坏 -> 保持简洁，避免过多兼容
**风险描述**: 接口变更可能影响现有调用方
**风险等级**: 低等
**缓解措施**:
- 保持现有API接口不变
- 新功能通过可选参数提供
- 充分的兼容性测试验证

### 风险3: 性能回归
**风险描述**: 新架构可能带来性能下降
**风险等级**: 低等
**缓解措施**:
- 建立性能基准测试
- 持续监控关键性能指标
- 预期通过时序优化实现性能提升

### Trade-off 1: 复杂度 vs 可维护性
**取舍**: 增加短期的架构复杂度，换取长期的可维护性

**分析**: 虽然引入分层架构会增加代码量，但通过清晰的职责分离，长期维护成本会显著降低

### Trade-off 2: 开发时间 vs 技术债务
**取舍**: 投入更多开发时间进行重构，以减少技术债务

**分析**: 当前技术债务已经严重影响开发效率，重构的长期收益远大于短期投入

## Migration Plan

### 阶段1: 基础设施建设 (第1-2周)
**目标**: 建立新架构的基础组件

**关键里程碑**:
- [ ] `WaitUtils` 工具类完成并通过测试
- [ ] `ScrapingUtils` 工具类完成并通过测试  
- [ ] 标准数据格式定义完成
- [ ] 配置管理系统重构完成

**验收标准**:
- 工具类单元测试覆盖率 ≥ 95%
- 性能测试显示等待机制优化效果
- 所有现有功能正常运行

### 阶段2: 三个 Scraper 核心逻辑重构 (第3-4周)
**目标**: 重构三个抓取器和服务逻辑

**关键里程碑**:
- [ ] **`SeerfarScraper` 重构完成，使用统一工具类和时序控制**
- [ ] **紧急补齐 `SeerfarScraper` 测试覆盖（从 0% 到 95%+）**
- [ ] `CompetitorDetectionService` 服务完成
- [ ] `OzonScraper` 重构完成，移除跟卖逻辑
- [ ] `CompetitorScraper` 专业化重构完成
- [ ] 服务协调层实现完成

**验收标准**:
- **SeerfarScraper 测试覆盖率 ≥ 95%**（当前几乎为 0%）
- 跟卖检测成功率 ≥ 95%
- 所有现有API保持兼容
- 三个 Scraper 集成测试全部通过

### 阶段3: 接口标准化 (第5周)
**目标**: 统一接口规范和异常处理

**关键里程碑**:
- [ ] 方法签名标准化完成
- [ ] 返回值格式统一完成
- [ ] 异常处理策略实现完成

**验收标准**:
- 接口文档更新完成
- 向后兼容性测试通过
- 代码审查通过

### 阶段4: 测试与优化 (第6周)
**目标**: 全面测试和性能优化

**关键里程碑**:
- [ ] **多 Scraper 集成测试完成**
- [ ] **SeerfarScraper → OzonScraper → CompetitorScraper 调用链测试**
- [ ] 端到端测试完成
- [ ] 性能回归测试完成
- [ ] 监控指标实现完成

**验收标准**:
- **整体测试覆盖率 ≥ 95%**（重点 SeerfarScraper 从 0% 提升）
- **集成测试覆盖率 ≥ 90%**
- 性能指标达到预期改进目标（响应时间提升 20-30%）
- 生产环境部署成功

### 回滚策略
**触发条件**:
- 关键功能失效
- 性能严重下降（>30%）
- 生产环境故障

**回滚步骤**:
1. 立即切换到备份分支
2. 验证核心功能正常
3. 分析失败原因
4. 制定修复计划

## Open Questions

### Q1: 是否需要引入缓存机制？ -> 不需要
**问题**: 重构后是否应该添加结果缓存来提高性能？

**考虑因素**:
- 跟卖数据实时性要求
- 缓存失效策略复杂度
- 内存使用量增加

**决策时间**: 阶段3开始前确定

### Q2: 监控指标的详细程度？-> 暂时不需要
**问题**: 需要监控哪些详细指标，如何平衡监控成本和收益？

**考虑因素**:
- 关键业务指标识别
- 监控数据存储成本
- 报警策略设计 

**决策时间**: 阶段3开始前确定

### Q3: 是否需要支持并发处理？-> 暂时不需要
**问题**: 虽然选择同步架构，但是否需要预留并发处理的扩展点？

**考虑因素**:
- 未来业务量增长预期
- 架构扩展的复杂度
- 性能提升的潜在收益

**决策时间**: 基于阶段4的性能测试结果决定