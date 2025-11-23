# Capability: 配置层架构

## ADDED Requirements

### Requirement: 配置按职责分层管理
配置层 SHALL 按职责分为四个独立目录，每个目录 MUST 承担单一职责，避免配置混乱和重复定义。

#### Scenario: 用户配置独立管理
- **GIVEN** CLI需要管理用户配置 (文件路径、筛选参数、输出设置)
- **WHEN** 导入用户配置
- **THEN** 用户配置位于 `cli/config/user_config.py`
- **AND** 可以通过 `from cli.config import UserConfig` 导入

#### Scenario: 系统配置独立管理
- **GIVEN** 系统需要管理浏览器、超时、性能、日志配置
- **WHEN** 导入系统配置
- **THEN** 系统配置位于 `common/config/system/` 目录
- **AND** 可以通过 `from common.config.system import BrowserConfig` 导入

#### Scenario: 业务配置独立管理
- **GIVEN** 业务层需要管理过滤、价格计算、Excel配置
- **WHEN** 导入业务配置
- **THEN** 业务配置位于 `common/config/business/` 目录
- **AND** 可以通过 `from common.config.business import FilterConfig` 导入

#### Scenario: 抓取配置独立管理
- **GIVEN** 抓取层需要管理选择器、货币、语言配置
- **WHEN** 导入抓取配置
- **THEN** 抓取配置位于 `common/config/scraping/` 目录
- **AND** 可以通过 `from common.config.scraping import OzonSelectorsConfig` 导入

### Requirement: 统一配置导出接口
配置层 MUST 通过 `common/config/__init__.py` 提供统一的导出接口，确保所有配置类 SHALL 可以通过 `from common.config import ...` 导入。

#### Scenario: 统一配置导入
- **GIVEN** 开发者需要导入多个配置类
- **WHEN** 使用 `from common.config import BrowserConfig, FilterConfig, OzonSelectorsConfig`
- **THEN** 所有配置类都可以成功导入
- **AND** 不需要知道配置类的具体文件位置

### Requirement: 消除配置重复定义
系统中 MUST NOT 存在重复的配置定义，店铺过滤参数、超时配置、浏览器配置 SHALL 只在一个位置定义。

#### Scenario: 店铺过滤参数唯一定义
- **GIVEN** 系统需要使用店铺过滤参数
- **WHEN** 导入过滤配置
- **THEN** 过滤参数只在 `common/config/business/filter_config.py` 中定义
- **AND** `cli/models.py` 中的重复定义已删除

#### Scenario: 超时配置唯一定义
- **GIVEN** 系统需要使用超时配置
- **WHEN** 导入超时配置
- **THEN** 超时参数只在 `common/config/system/timeout_config.py` 中定义
- **AND** `common/config.py` 中的重复定义已删除

### Requirement: 配置验证机制
所有配置类 MUST 实现验证方法，SHALL 在初始化时自动验证配置参数的合法性。

#### Scenario: 配置参数范围验证
- **GIVEN** 创建配置实例时传入参数
- **WHEN** 参数超出合法范围 (如负数超时时间)
- **THEN** 抛出 ConfigurationError 异常
- **AND** 错误信息明确指出哪个参数不合法

#### Scenario: 配置必填字段验证
- **GIVEN** 创建配置实例时缺少必填字段
- **WHEN** 初始化配置对象
- **THEN** 抛出 ConfigurationError 异常
- **AND** 错误信息列出所有缺失的必填字段

### Requirement: 配置层测试覆盖率
配置层 MUST 有完整的单元测试覆盖，SHALL 确保所有配置类的验证逻辑正确，测试覆盖率 MUST ≥ 95%。

#### Scenario: 用户配置测试覆盖
- **GIVEN** 用户配置文件 `cli/config/user_config.py`
- **WHEN** 运行测试覆盖率检查
- **THEN** 测试覆盖率 ≥ 95%
- **AND** 所有配置字段的验证逻辑都有测试

#### Scenario: 配置验证测试覆盖
- **GIVEN** 所有配置类的验证方法
- **WHEN** 运行配置验证测试
- **THEN** 测试覆盖率 = 100%
- **AND** 所有边界条件和异常情况都有测试

#### Scenario: 总体测试覆盖率
- **GIVEN** 整个配置层 `common/config/` 和 `cli/config/`
- **WHEN** 运行 `pytest --cov=common/config --cov=cli/config`
- **THEN** 总体测试覆盖率 ≥ 95%
- **AND** 所有关键配置类都有完整测试

## MODIFIED Requirements

### Requirement: 配置导入路径
所有配置类 SHALL 通过 `common/config/__init__.py` 统一导出，MUST 支持统一的导入方式 `from common.config import ...`，同时 SHALL 保持向后兼容的导入路径。

#### Scenario: 业务层导入配置
- **GIVEN** 业务层需要导入多个配置类
- **WHEN** 使用 `from common.config import FilterConfig, PriceCalculationConfig`
- **THEN** 所有配置类都可以成功导入
- **AND** 不需要关心配置类的具体文件位置

#### Scenario: 旧代码兼容性
- **GIVEN** 旧代码使用 `from common.config import GoodStoreSelectorConfig`
- **WHEN** 执行导入操作
- **THEN** 导入仍然成功 (通过__init__.py转发)
- **AND** 配置类从新位置加载

## REMOVED Requirements

### Requirement: 单文件配置定义
**原因**: 单文件 (common/config.py, 473行) 混合了业务配置、系统配置、浏览器配置、Excel配置，违反单一职责原则

**迁移**: 
- 用户配置 → `cli/config/user_config.py`
- 系统配置 → `common/config/system/` (browser, timeout, performance, logging)
- 业务配置 → `common/config/business/` (filter, price, excel)
- 抓取配置 → `common/config/scraping/` (已存在，重组)

### Requirement: 配置重复定义
**原因**: 店铺过滤参数在 common/config.py 和 cli/models.py 中重复，超时配置在多处重复

**迁移**:
- 店铺过滤参数 → 只保留在 `common/config/business/filter_config.py`
- 超时配置 → 只保留在 `common/config/system/timeout_config.py`
- cli/models.py 中的业务配置字段删除，只保留UI状态类

### Requirement: 配置文件分散
**原因**: common/logging_config.py 独立存在，应该归入系统配置目录

**迁移**:
- `common/logging_config.py` → `common/config/system/logging_config.py`
- 通过 `common/config/__init__.py` 保持向后兼容导入

## ADDED Requirements

### Requirement: 测试用例更新和完善
所有测试用例 MUST 更新为使用新的统一导入路径，SHALL 补充配置验证和新增功能的测试，确保测试覆盖率 MUST ≥ 95%。

#### Scenario: 更新测试导入路径
- **GIVEN** 测试文件使用老旧导入路径
- **WHEN** 更新测试用例
- **THEN** 所有模型导入更新为 `from common.models import`
- **AND** 所有配置导入更新为 `from common.config import`
- **AND** 测试仍然通过

#### Scenario: 补充配置验证测试
- **GIVEN** 配置类新增了验证方法
- **WHEN** 更新配置测试
- **THEN** 所有配置类的验证逻辑都有测试
- **AND** 测试覆盖参数范围检查、必填字段检查
- **AND** 测试覆盖所有异常情况

#### Scenario: 完善测试覆盖
- **GIVEN** 现有测试覆盖率不足
- **WHEN** 补充测试用例
- **THEN** 每个配置类的所有字段都有测试
- **AND** 每个配置目录(user/system/business/scraping)都有完整测试
- **AND** 总体测试覆盖率 ≥ 95%

### Requirement: 代码清理和质量保证
系统 MUST 清理所有冗余和过时的代码，SHALL 使用自动化工具检测未使用的导入、死代码和重复代码，确保代码质量达到零 lint 错误。

#### Scenario: 清理禁用的测试文件
- **GIVEN** 存在 .disabled 测试文件
- **WHEN** 审查测试目录
- **THEN** 决定恢复或永久删除这些测试
- **AND** 如果恢复，更新为使用新的导入路径

#### Scenario: 移除未使用的导入
- **GIVEN** 代码中存在未使用的导入语句
- **WHEN** 运行 autoflake 检查
- **THEN** 自动移除所有未使用的导入
- **AND** 代码仍然正常运行

#### Scenario: 检测死代码
- **GIVEN** 代码中存在从未被调用的函数或类
- **WHEN** 运行 vulture 检测 (min-confidence 80)
- **THEN** 识别出所有死代码
- **AND** 决定删除或添加使用场景

#### Scenario: 消除重复代码
- **GIVEN** 代码中存在重复的代码块
- **WHEN** 运行 pylint 重复代码检测
- **THEN** 识别出所有重复代码
- **AND** 提取为公共函数或类

#### Scenario: 零lint错误
- **GIVEN** 完成所有代码清理
- **WHEN** 运行完整 lint 检查
- **THEN** 零 lint 错误
- **AND** 零 lint 警告 (或已确认可忽略)

### Requirement: 项目文档架构更新
openspec/project.md MUST 完整更新模型和配置架构章节，SHALL 反映新的目录结构、职责分离和模块依赖关系。

#### Scenario: 模型架构文档更新
- **GIVEN** project.md需要反映新的模型架构
- **WHEN** 更新"模块架构"章节
- **THEN** 文档包含完整的6文件模型结构说明
- **AND** 包含职责分离原则和导入示例
- **AND** 包含模型层的测试覆盖率要求

#### Scenario: 配置架构文档更新
- **GIVEN** project.md需要反映新的配置架构
- **WHEN** 更新"配置管理"章节
- **THEN** 文档包含完整的4目录配置结构说明
- **AND** 包含用户/系统/业务/抓取配置的详细职责
- **AND** 包含配置验证机制说明

#### Scenario: 模块依赖关系图更新
- **GIVEN** project.md包含模块依赖关系图
- **WHEN** 更新依赖关系图
- **THEN** 图中反映新的模型和配置结构
- **AND** 清晰展示CLI层、业务层、抓取层、工具层的依赖关系
- **AND** 标注模型和配置的流向
