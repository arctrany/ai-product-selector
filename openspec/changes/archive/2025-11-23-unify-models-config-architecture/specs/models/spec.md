# Capability: 模型层架构

## ADDED Requirements

### Requirement: 统一模型包结构
模型层 SHALL 按职责拆分为独立文件，每个文件 MUST 承担单一职责，避免职责混乱和重复定义。

#### Scenario: 枚举类独立管理
- **GIVEN** 系统需要使用枚举类型 (StoreStatus, GoodStoreFlag, ScrapingStatus)
- **WHEN** 开发者导入枚举类
- **THEN** 所有枚举类集中在 `common/models/enums.py` 文件中
- **AND** 可以通过 `from common.models import StoreStatus` 导入

#### Scenario: 业务模型独立管理
- **GIVEN** 系统需要使用业务领域模型 (StoreInfo, ProductInfo, 等6个类)
- **WHEN** 开发者导入业务模型
- **THEN** 所有业务模型集中在 `common/models/business_models.py` 文件中
- **AND** 可以通过 `from common.models import StoreInfo` 导入

### Requirement: 统一导出接口
模型层 MUST 通过 `common/models/__init__.py` 提供统一的导出接口，确保所有模型类 SHALL 可以通过 `from common.models import ...` 导入。

#### Scenario: 单一导入路径
- **GIVEN** 开发者需要导入多个模型类
- **WHEN** 使用 `from common.models import StoreInfo, ProductInfo, ScrapingResult`
- **THEN** 所有模型类都可以成功导入
- **AND** 不需要知道模型类的具体文件位置

### Requirement: 消除ScrapingResult重复定义
系统中 MUST 只存在一个ScrapingResult定义，SHALL 使用新版本 (7个字段)，旧版本 (4个字段) MUST 删除。

#### Scenario: 只有新版本ScrapingResult
- **GIVEN** 开发者导入 ScrapingResult
- **WHEN** 使用 `from common.models import ScrapingResult`
- **THEN** 导入的是新版本 (包含 status, metadata, timestamp 字段)
- **AND** 旧版本 (只有 success, data, error_message, execution_time) 不存在

### Requirement: 工具函数位置合理化
模型文件中 MUST NOT 包含工具函数，所有工具函数 SHALL 迁移到 `common/utils/` 目录。

#### Scenario: 验证函数位于utils
- **GIVEN** 系统需要使用验证函数 (validate_store_id, validate_price, validate_weight)
- **WHEN** 导入验证函数
- **THEN** 函数位于 `common/utils/model_utils.py`
- **AND** 可以通过 `from common.utils.model_utils import validate_store_id` 导入

### Requirement: 模型层测试覆盖率
模型层 MUST 有完整的单元测试覆盖，SHALL 确保所有模型类和导入路径的正确性，测试覆盖率 MUST ≥ 95%。

#### Scenario: 枚举类测试覆盖
- **GIVEN** 枚举类文件 `common/models/enums.py`
- **WHEN** 运行测试覆盖率检查
- **THEN** 测试覆盖率 = 100%
- **AND** 所有枚举值和字符串转换都有测试

#### Scenario: 总体测试覆盖率
- **GIVEN** 整个模型层 `common/models/`
- **WHEN** 运行 `pytest --cov=common/models`
- **THEN** 总体测试覆盖率 ≥ 95%
- **AND** 所有关键模型类都有完整测试

## MODIFIED Requirements

### Requirement: 模型导入路径
所有模型类 SHALL 通过 `common/models/__init__.py` 统一导出，MUST 支持统一的导入方式 `from common.models import ...`，同时 SHALL 保持向后兼容的导入路径。

#### Scenario: 业务层导入模型
- **GIVEN** 业务层需要导入多个模型类
- **WHEN** 使用 `from common.models import StoreInfo, ProductInfo, PriceCalculationResult`
- **THEN** 所有模型类都可以成功导入
- **AND** 不需要关心模型类的具体文件位置

## ADDED Requirements

### Requirement: 测试用例更新和完善
所有测试用例 MUST 更新为使用新的模型和配置导入路径，SHALL 补充新增字段和验证逻辑的测试，确保测试覆盖率 MUST ≥ 95%。

#### Scenario: 更新测试导入路径
- **GIVEN** 测试用例使用老旧导入路径
- **WHEN** 更新测试文件
- **THEN** 所有导入改为 `from common.models import`
- **AND** 所有配置导入改为 `from common.config import`
- **AND** 测试仍然通过

#### Scenario: 补充ScrapingResult新字段测试
- **GIVEN** ScrapingResult新增了status, metadata, timestamp字段
- **WHEN** 更新抓取相关测试
- **THEN** 所有测试验证新字段的正确性
- **AND** 测试工厂方法 create_success/create_failure
- **AND** 测试 to_dict() 转换方法

#### Scenario: 补充配置验证逻辑测试
- **GIVEN** 所有配置类新增了验证方法
- **WHEN** 更新配置相关测试
- **THEN** 所有测试验证参数范围检查
- **AND** 测试必填字段检查
- **AND** 测试边界条件和异常情况

#### Scenario: 完善现有测试覆盖
- **GIVEN** 现有测试覆盖率不足
- **WHEN** 补充测试用例
- **THEN** 每个模型类的所有方法都有测试
- **AND** 每个配置类的所有字段都有测试
- **AND** 总体测试覆盖率 ≥ 95%

### Requirement: 项目文档架构更新
openspec/project.md MUST 更新模型和配置架构章节，反映新的目录结构和职责分离。

#### Scenario: 更新模型架构文档
- **GIVEN** project.md包含旧的模型架构说明
- **WHEN** 更新文档
- **THEN** 文档反映新的6文件模型结构
- **AND** 包含完整的职责说明和导入示例

#### Scenario: 更新配置架构文档
- **GIVEN** project.md包含旧的配置架构说明
- **WHEN** 更新文档
- **THEN** 文档反映新的4目录配置结构
- **AND** 包含用户/系统/业务/抓取配置的详细说明

#### Scenario: 更新模块依赖关系图
- **GIVEN** project.md包含旧的依赖关系图
- **WHEN** 更新文档
- **THEN** 依赖关系图反映新的模型和配置结构
- **AND** 清晰展示各层之间的依赖关系

## REMOVED Requirements

### Requirement: 单文件模型定义
**原因**: 单文件 (common/models.py, 345行) 混合了业务模型、抓取模型、异常类、工具函数，违反单一职责原则

**迁移**: 
- 业务模型 → `common/models/business_models.py`
- 抓取模型 → `common/models/scraping_models.py`
- 异常类 → `common/models/exceptions.py`
- 枚举类 → `common/models/enums.py`
- 工具函数 → `common/utils/model_utils.py` 和 `common/utils/scraping_utils.py`
