# Testing Specification

## Purpose
This specification defines comprehensive testing organization, structure, and practices for the AI Product Selector project to ensure consistent, maintainable, and reliable test execution across all platforms and modules.

## Requirements

### Requirement: 测试目录结构规范
测试目录结构 MUST 与源代码目录结构一一对应，确保测试文件组织的一致性和可维护性。

#### Scenario: 源代码模块对应测试目录
- **WHEN** 源代码包含模块目录如cli/, common/, task_manager/
- **THEN** 测试目录 MUST 包含对应的tests/cli/, tests/common/, tests/task_manager/

#### Scenario: 单文件模块对应测试文件
- **WHEN** 源代码包含单文件模块如good_store_selector.py
- **THEN** 测试文件 MUST 命名为tests/test_good_store_selector.py

### Requirement: 测试文件命名规范
测试文件命名 MUST 遵循统一规范，禁止创建多版本测试文件。

#### Scenario: 标准测试文件命名
- **WHEN** 为模块创建测试文件
- **THEN** 文件名 MUST 以test_开头，如test_module_name.py

#### Scenario: 禁止多版本测试文件
- **WHEN** 需要修改或增强测试
- **THEN** MUST 直接修改原测试文件，不得创建test_XXX_fixed.py、test_XXX_real.py等版本

### Requirement: 测试分类组织
测试 MUST 按照类型进行分类组织，确保测试执行效率和维护性。

#### Scenario: 单元测试组织
- **WHEN** 编写单元测试
- **THEN** 测试文件 MUST 位于对应模块的测试目录下

#### Scenario: 集成测试组织  
- **WHEN** 编写跨模块集成测试
- **THEN** 测试文件 MUST 使用test_integration_前缀并说明集成范围

#### Scenario: 端到端测试组织
- **WHEN** 编写端到端测试
- **THEN** 测试文件 MUST 使用test_end_to_end_前缀并位于tests/根目录

### Requirement: 跨平台兼容性
测试 MUST 确保在Windows、Linux、macOS平台上正常执行。

#### Scenario: 路径处理兼容性
- **WHEN** 测试涉及文件路径操作
- **THEN** MUST 使用pathlib.Path而非硬编码路径

#### Scenario: 平台特定测试跳过
- **WHEN** 测试功能在特定平台不适用
- **THEN** MUST 使用@pytest.mark.skipif进行平台条件跳过

### Requirement: 测试执行标准
测试 MUST 满足执行成功率和覆盖率要求。

#### Scenario: 单元测试成功率
- **WHEN** 执行单元测试套件
- **THEN** 成功率 MUST 达到95%以上

#### Scenario: 端到端测试成功率
- **WHEN** 执行端到端测试
- **THEN** 关键业务流程测试成功率 MUST 达到90%以上
