# Change: 统一模型和配置架构 - 消除重复定义和职责混乱

## Why

### 模型层核心问题
1. **ScrapingResult重复定义**: `common/models.py:210` 和 `common/models/scraping_result.py:23` 存在两个版本，新版本有7个字段，旧版本只有4个字段，导致潜在的类型混乱
2. **职责混乱**: `common/models.py` (345行) 混合了业务模型、抓取模型、异常类、工具函数，违反单一职责原则
3. **导入混乱**: `ScrapingOrchestrator` 同时从旧模型包和新模型包导入，说明重构未完成
4. **维护困难**: 18个类+4个工具函数挤在一个文件中，难以定位和修改
5. **测试覆盖不足**: 模型层几乎无单元测试，覆盖率≈0%

### 配置层核心问题
1. **配置重复定义**: 店铺过滤参数在 `common/config.py` 和 `cli/models.py` 中重复，超时配置在 `BrowserConfig` 和 `timeout_config.py` 中重复
2. **职责混乱**: `common/config.py` (473行) 混合了业务配置、浏览器配置、Excel配置、日志配置，`cli/models.py` 混合了UI状态和业务配置
3. **导入混乱**: 34处配置导入引用，不清楚应该从哪里导入配置
4. **配置分散**: 2207行配置代码分散在11个文件中，缺乏统一管理
5. **边界不清**: 用户配置、系统配置、业务配置、抓取配置混在一起
6. **测试覆盖不足**: 配置层几乎无单元测试，配置验证缺失

### CLI/Task/Common模块间严重冲突和冗余问题 (CRITICAL - 零容忍)

经过深度调研发现，CLI、Task、Common三个模块存在**严重的配置重复、职责混乱和命名冲突**，违反独立模块化的零冲突原则：

#### 配置严重重复 (CRITICAL)
1. **UIConfig vs GoodStoreSelectorConfig 字段完全重复**:
   - `UIConfig.min_store_sales_30days` ↔ `GoodStoreSelectorConfig.selector_filter.store_min_sales_30days`
   - `UIConfig.min_store_orders_30days` ↔ `GoodStoreSelectorConfig.selector_filter.store_min_orders_30days` 
   - `UIConfig.margin` ↔ `GoodStoreSelectorConfig.selector_filter.profit_rate_threshold`
   - **风险**: 两套配置系统需手动同步，易出现不一致导致业务逻辑错误

2. **BrowserConfig vs ScrapingConfig 新旧并存冗余**:
   - 完全相同功能的两套配置类，`scraping`字段向后兼容`browser`字段
   - **问题**: 系统需同时维护两套配置，增加复杂度和维护成本

#### 职责严重混乱 (CRITICAL)
1. **Common模块职责过重**:
   - `common/task_control.py` → **应该属于Task模块**
   - `common/logging_config.py` → **应该属于CLI应用层**
   - CLI特定的`dryrun`、`selection_mode`参数 → **散落在Common配置中**

2. **业务逻辑与配置混合**:
   - `PriceCalculationConfig`包含具体业务计算规则，违反配置与逻辑分离原则
   - `SelectorFilterConfig`包含业务判定阈值，应该是策略而非配置

#### 命名冲突 (HIGH)
1. **字段命名不一致**:
   - `browser` vs `scraping` 字段并存造成混淆
   - `timeout_seconds` vs `page_load_timeout` vs `element_wait_timeout` 语义重叠
   - `max_retries` vs `max_retry_attempts` 表示相同含义

2. **配置层次混乱**:
   - CLI层、系统层、业务层配置边界不清晰
   - 多层配置管理导致维护困难

### 业务影响
- **风险**: good_store_selector.py 核心流程依赖7个模型类和多个配置类，任何导入错误都会中断整个系统
- **技术债**: 19处模型导入+34处配置导入，重构成本高
- **质量问题**: 无测试保护，模型和配置变更容易引入回归
- **🚨架构风险**: 配置重复和职责混乱导致系统难以维护，违反独立模块化原则

## What Changes

重新设计模型和配置架构，实现**独立模块化**并按职责清晰分离。

### 核心设计原则

- **独立模块化**: 每个模块(cli、task、rpa、common)拥有独立的models.py、config.py、config/目录
- **命名空间隔离**: 通过类名前缀和模块路径避免冲突
- **分层依赖管理**: common(基础层) → rpa/task(中间层) → cli(应用层)
- **最小改动原则**: 保持现有接口兼容，支持渐进式迁移

### 独立模块化重构

**新架构目标**:
```
project/
├── cli/
│   ├── models.py      # CliAppState, CliLogEntry, CliUIConfig
│   ├── config.py      # CliUserConfig, CliSystemConfig  
│   └── config/        # CLI专用配置目录
├── task_manager/      # 新独立模块
│   ├── models.py      # TaskInfo, TaskStatus, TaskConfig
│   ├── config.py      # TaskManagerConfig, ExecutionConfig
│   └── config/        # Task管理配置目录  
└── common/
    ├── models.py      # CommonStoreInfo, CommonProductInfo (共享基础模型)
    ├── config.py      # CommonSystemConfig (共享基础配置)
    └── config/        # 共享配置目录

注: RPA模块已成熟稳定，保持现有架构不做任何更改
```

### 命名冲突避免策略

1. **类名前缀策略**: CliConfig, TaskConfig, CommonConfig
2. **命名空间导入**: 明确模块路径导入，避免名称冲突  
3. **接口抽象**: 定义统一接口，各模块实现自己的版本
4. **配置继承**: 共享配置作为基类，模块配置继承扩展

### 旧架构清除策略

**彻底清除旧架构**，避免新旧两套并存：
1. **直接替换**: 移除`common/models.py`和`common/config.py`旧文件
2. **统一导入**: 更新所有导入语句使用新的命名空间
3. **清理兼容**: 移除所有向后兼容的转发机制  
4. **分步实施**: 按模块逐步迁移，确保风险可控

### 模型层文件结构变更

#### 新增文件
1. `common/models/enums.py` - 所有枚举类 (StoreStatus, GoodStoreFlag, ScrapingStatus)
2. `common/models/business_models.py` - 业务领域模型 (StoreInfo, ProductInfo, 等6个类)
3. `common/models/scraping_models.py` - 抓取领域模型 (ScrapingResult新版, CompetitorInfo, 等5个类)
4. `common/models/excel_models.py` - Excel数据模型 (ExcelStoreData)
5. `common/models/exceptions.py` - 所有异常类 (7个异常类)
6. `common/utils/model_utils.py` - 模型工具函数 (validate_*, format_*, calculate_*)

#### 修改文件
1. `common/models/__init__.py` - 统一导出接口，保证向后兼容
2. `common/models/scraping_result.py` - 保留作为废弃别名文件
3. `common/utils/scraping_utils.py` - 新增 clean_price_string 函数

#### 删除文件
1. `common/models.py` - 旧模型文件 (345行)

### 模块配置分离策略

#### 新增独立模块配置目录和文件
1. `cli/config/` - CLI配置目录
   - `cli/config/user_config.py` - 用户配置 (文件路径、筛选参数、输出设置)
   - `cli/config/__init__.py` - 统一导出接口

2. `common/config/system/` - 系统配置目录
   - `common/config/system/browser_config.py` - 浏览器配置
   - `common/config/system/timeout_config.py` - 超时配置 (从根目录迁移)
   - `common/config/system/performance_config.py` - 性能配置
   - `common/config/system/logging_config.py` - 日志配置 (从根目录迁移)
   - `common/config/system/__init__.py` - 统一导出接口

3. `common/config/business/` - 业务配置目录
   - `common/config/business/filter_config.py` - 过滤配置
   - `common/config/business/price_config.py` - 价格计算配置
   - `common/config/business/excel_config.py` - Excel配置
   - `common/config/business/__init__.py` - 统一导出接口

4. `common/config/` - 共享配置目录 (基础层)
   - `common/config.py` - CommonSystemConfig, CommonBusinessConfig
   - `common/config/system/` - 系统级共享配置
   - `common/config/business/` - 业务级共享配置
   - `common/config/scraping/` - 抓取配置 (保留现有文件)

#### 修改文件
1. `common/config/__init__.py` - 重构为统一配置入口，导出所有配置类
2. `cli/models.py` - 删除 UIConfig 中的业务配置字段，只保留UI状态类

#### 删除文件
1. `common/config.py` - 旧配置文件 (473行)
2. `common/logging_config.py` - 迁移到 system/logging_config.py

### 模型迁移映射

| 原位置 (common/models.py) | 新位置 | 数量 |
|---------------------------|--------|------|
| StoreStatus, GoodStoreFlag | enums.py | 2个枚举 |
| StoreInfo, ProductInfo, ... | business_models.py | 6个业务类 |
| ScrapingResult (旧版) | **删除** (保留新版) | - |
| CompetitorStore | scraping_models.py | 1个抓取类 |
| ExcelStoreData | excel_models.py | 1个Excel类 |
| 7个异常类 | exceptions.py | 7个异常 |
| 4个工具函数 | utils/model_utils.py | 4个函数 |
| clean_price_string | utils/scraping_utils.py | 1个函数 |

### 配置迁移映射

| 原位置 | 新位置 | 说明 |
|-------|--------|------|
| common/config.py::SelectorFilterConfig | common/config/business/filter_config.py | 业务过滤配置 |
| common/config.py::PriceCalculationConfig | common/config/business/price_config.py | 价格计算配置 |
| common/config.py::BrowserConfig | common/config/system/browser_config.py | 浏览器配置 |
| common/config.py::ExcelConfig | common/config/business/excel_config.py | Excel配置 |
| common/config.py::LoggingConfig | common/config/system/logging_config.py | 日志配置 |
| common/config.py::PerformanceConfig | common/config/system/performance_config.py | 性能配置 |
| common/config.py::ScrapingConfig | **删除** (合并到 base_scraping_config) | - |
| common/logging_config.py | common/config/system/logging_config.py | 合并日志配置 |
| common/config/timeout_config.py | common/config/system/timeout_config.py | 移动到system目录 |
| cli/models.py::UIConfig (业务字段) | cli/config/user_config.py | 提取业务配置 |

### 向后兼容保证

#### 模型层兼容
```python
# 场景1: 从 common.models 导入 (19处引用)
from common.models import StoreInfo, ProductInfo, ScrapingResult
# ✅ 通过 __init__.py 自动转发到新文件

# 场景2: 从 scraping_result 导入 (6处引用)  
from common.models.scraping_result import ScrapingResult
# ✅ 保留别名文件，标记为废弃但继续工作
```

#### 配置层兼容
```python
# 场景1: 从 common.config 导入 (34处引用)
from common.config import GoodStoreSelectorConfig
# ✅ 通过 __init__.py 自动转发到新位置

# 场景2: 从 common.config 导入具体配置类
from common.config import BrowserConfig, PriceCalculationConfig
# ✅ 通过 __init__.py 转发到 system/browser_config.py 和 business/price_config.py
```

## Impact

### 受影响的规范
- **更新**: `unified-models-config` - 独立模块化的模型和配置管理能力规范

### 受影响的代码
- **重构**: `common/models.py` → 保留共享基础模型，各模块创建独立models.py
- **重构**: `common/config.py` → 保留共享基础配置，各模块创建独立config.py  
- **新增**: `cli/models.py`, `cli/config.py`, `cli/config/` - CLI独立模型配置
- **新增**: `task_manager/models.py`, `task_manager/config.py`, `task_manager/config/` - 任务管理独立模块
- **移除**: `common/models.py`, `common/config.py` - 旧架构文件完全清除
- **更新**: 所有模块间引用更新为命名空间隔离的导入方式
- **增强**: 每个模块的独立测试覆盖
- **保护**: RPA模块保持现有架构，不做任何更改

### 影响的代码 (Files)

#### 模型层影响 (14个文件)
**业务层** (3个文件):
- `business/pricing_calculator.py` - 导入 PriceCalculationResult
- `business/profit_evaluator.py` - 导入 ProductInfo, PriceCalculationResult
- `business/store_evaluator.py` - 导入 StoreInfo, StoreAnalysisResult, ProductAnalysisResult

**抓取层** (4个文件):
- `common/scrapers/competitor_scraper.py` - 导入 CompetitorStore, clean_price_string
- `common/scrapers/seerfar_scraper.py` - 导入 ScrapingResult
- `common/scrapers/erp_plugin_scraper.py` - 导入 ScrapingResult
- `common/services/scraping_orchestrator.py` - 导入17个类 (最复杂)

**主流程** (1个文件):
- `good_store_selector.py` - 导入7个核心业务模型

**测试层** (6个文件):
- `tests/test_selection_modes.py`
- `tests/test_selection_modes_real.py`
- `tests/test_base_scraper.py`
- `tests/test_seerfar_scraper.py`
- `tests/test_erp_plugin_scraper.py`
- `tests/test_scraping_integration.py`

#### 配置层影响 (估计20+个文件)
- 所有导入 `from common.config import ...` 的文件
- 所有使用 `GoodStoreSelectorConfig` 的文件
- `cli/` 目录下所有使用配置的文件

### 不影响的代码
- ✅ `rpa/browser/core/models/` - RPA技术层，完全隔离
- ✅ `cli/models.py` 的UI状态类 (AppState, LogLevel, ProgressInfo, LogEntry, UIStateManager) - 保持独立

### 迁移影响分析
- **彻底清除**: 完全移除旧架构文件，避免新旧并存维护负担
- **直接替换**: 核心业务逻辑直接迁移到新架构，降低长期维护成本
- **分步实施**: 按模块逐步迁移，确保风险可控
- **依赖解耦**: 减少模块间配置耦合度 ≥ 80%
- **冲突消除**: 100%消除model和config命名冲突

### 质量改进目标
- **模块独立度**: CLI、Task、Common三模块model/config完全独立，零冲突
- **架构统一**: 统一使用新架构，无兼容性维护负担
- **测试覆盖率**: 每个模块达到 ≥ 95%  
- **代码重复度**: 减少 ≥ 60% (消除重复定义)
- **导入一致性**: 100% 使用命名空间隔离导入
- **RPA保护**: RPA模块保持100%稳定，不受重构影响

## Migration Path

### Phase 1: 模型层准备阶段 (无破坏性)
1. 创建新的模型文件 (enums.py, business_models.py, scraping_models.py, excel_models.py, exceptions.py)
2. 复制内容到新文件 (保留旧文件)
3. 更新 models/__init__.py 导出新文件内容
4. **验证**: 所有现有导入路径仍然工作

### Phase 2: 配置层准备阶段 (无破坏性)
1. 创建新的配置目录结构 (cli/config, system, business, scraping)
2. 复制配置类到新文件 (保留旧文件)
3. 更新 config/__init__.py 导出新文件内容
4. **验证**: 所有现有配置导入路径仍然工作

### Phase 3: 工具函数迁移
1. 创建 common/utils/model_utils.py
2. 移动验证和格式化函数
3. 移动 clean_price_string 到 scraping_utils.py
4. 更新 __init__.py 导出工具函数 (兼容)
5. **验证**: competitor_scraper.py 等文件仍然工作

### Phase 4: 删除旧文件
1. 删除 common/models.py (旧模型文件)
2. 删除 common/config.py (旧配置文件)
3. 删除 common/logging_config.py (已迁移)
4. 保留 scraping_result.py 作为别名文件
5. **验证**: 运行完整测试套件

### Phase 5: 测试覆盖 (模型层)
1. 创建 tests/test_models_enums.py
2. 创建 tests/test_models_business.py
3. 创建 tests/test_models_scraping.py
4. 创建 tests/test_models_compatibility.py
5. **目标**: 模型层测试覆盖率 ≥ 95%

### Phase 6: 测试覆盖 (配置层)
1. 创建 tests/test_config_user.py
2. 创建 tests/test_config_system.py
3. 创建 tests/test_config_business.py
4. 创建 tests/test_config_scraping.py
5. 创建 tests/test_config_compatibility.py
6. 创建 tests/test_config_validation.py
7. **目标**: 配置层测试覆盖率 ≥ 95%

### Phase 7: 集成测试
1. 创建 tests/test_good_store_selector_integration.py
2. 创建 tests/test_config_loading_integration.py
3. 测试完整的配置加载和模型使用流程
4. **目标**: 集成测试覆盖率 ≥ 90%

### Phase 8: 更新和完善所有测试用例
1. 审查 tests/ 目录下所有测试文件
2. 更新测试用例使用新的模型和配置导入路径
3. 完善测试用例覆盖新增的模型字段和配置验证
4. 补充缺失的测试场景
5. 确保所有测试通过且覆盖率达标

### Phase 9: 文档更新
1. 更新 openspec/project.md 的模型架构章节
2. 更新 openspec/project.md 的配置架构章节
3. 更新 openspec/project.md 的模块依赖关系图
4. 创建迁移指南 (如何更新导入路径)
5. 标记废弃的导入路径

### Phase 10: 代码清理和质量检查
1. 提交已删除文件的变更 (common/interfaces/scraper_interface.py)
2. 审查并处理禁用的测试文件 (test_ozon_calculator.py.disabled, test_erp_ozon_integration.py.disabled)
3. 清理未跟踪的临时文件和缓存
4. 运行 autoflake 检查并移除未使用的导入
5. 运行 vulture 检测并移除死代码
6. 运行 pylint 检测并消除重复代码
7. 验证所有文件都有明确用途和文档
8. 运行完整的 lint 和类型检查
9. 确保零 lint 错误和警告
10. 提交最终清理变更

## Risks

### 高风险
1. **ScrapingResult字段不兼容** - 新版本7个字段 vs 旧版本4个字段
   - 缓解: 额外字段都有默认值，工厂方法保证兼容
2. **good_store_selector.py核心流程中断** - 依赖7个模型类和多个配置类
   - 缓解: Phase 1-2不删除旧文件，完整集成测试覆盖
3. **配置重复定义冲突** - cli/models.py 和 common/config.py 中的重复字段
   - 缓解: 先提取到新位置，再逐步删除旧位置，保持向后兼容
4. **循环导入问题** - 模型和配置文件之间可能产生循环依赖
   - 缓解: 严格职责分离，避免相互引用

### 中风险
1. **测试文件导入路径错误** - 6个测试文件需要更新模型导入
   - 缓解: 向后兼容策略保证旧导入路径仍然工作
2. **配置导入路径错误** - 34处配置导入需要验证
   - 缓解: __init__.py保留导出，专门的兼容性测试验证
3. **clean_price_string迁移影响** - competitor_scraper.py直接导入
   - 缓解: __init__.py保留导出，专门的单元测试验证

### 回滚计划
- Phase 1-2失败: 删除新文件，恢复__init__.py
- Phase 3失败: 恢复工具函数到models.py
- Phase 4失败: 恢复common/models.py和common/config.py
- Phase 5-7失败: 测试失败不影响生产代码，可独立修复

## Success Criteria

### 功能标准
- ✅ 所有现有导入路径继续工作 (19处模型导入+34处配置导入，零修改)
- ✅ good_store_selector.py 完整流程正常运行
- ✅ ScrapingOrchestrator 正常工作
- ✅ 所有业务层 (business/) 功能正常
- ✅ 所有抓取层 (common/scrapers/) 功能正常
- ✅ CLI配置加载和使用正常
- ✅ 所有测试通过 (包括新增测试)

### 质量标准
- ✅ 模型层测试覆盖率 ≥ 95%
- ✅ 配置层测试覆盖率 ≥ 95%
- ✅ 集成测试覆盖率 ≥ 90%
- ✅ 配置验证测试覆盖所有配置类
- ✅ 零 lint 错误
- ✅ 文档完整 (每个模型类和配置类有文档字符串)

### 架构标准
- ✅ 模型职责清晰分离 (业务/抓取/异常/枚举)
- ✅ 配置职责清晰分离 (用户/系统/业务/抓取)
- ✅ 无重复定义 (ScrapingResult只有一个版本，配置参数不重复)
- ✅ 工具函数位置合理 (在utils/中)
- ✅ 导出接口统一 (通过__init__.py)
- ✅ 配置验证机制完善 (所有配置类有验证方法)

## Estimated Effort
- **模型层准备**: 2小时 (10个任务)
- **配置层准备**: 3小时 (15个任务)
- **工具函数迁移**: 1小时 (6个任务)
- **删除旧文件**: 0.5小时 (5个任务)
- **模型层测试**: 4小时 (20个任务)
- **配置层测试**: 5小时 (30个任务)
- **集成测试**: 3小时 (10个任务)
- **更新和完善所有测试**: 3小时 (15个任务)
- **文档更新**: 2小时 (10个任务)
- **代码清理和质量检查**: 2小时 (10个任务)
- **总计**: 25.5小时 (136个任务)
