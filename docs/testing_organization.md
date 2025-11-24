# 测试组织规范和目录结构映射方案

## 1. 源代码与测试目录的一一对应关系

### 目录结构映射原则
- 每个源代码模块都有对应的测试目录
- 测试目录结构与源代码目录结构保持一致
- 测试文件放置在与被测试源文件相对应的测试目录中

### 目录映射示例
```
源代码目录结构:
├── cli/
│   ├── main.py
│   └── models.py
├── common/
│   ├── models/
│   │   ├── enums.py
│   │   └── excel_models.py
│   ├── config/
│   │   └── base_config.py
│   └── utils/
│       └── wait_utils.py
├── rpa/
│   └── browser/
│       └── browser_service.py
└── task_manager/
    ├── controllers.py
    └── models.py

对应的测试目录结构:
├── tests/
│   ├── cli/
│   │   ├── test_main.py
│   │   └── test_models.py
│   ├── common/
│   │   ├── models/
│   │   │   ├── test_enums.py
│   │   │   └── test_excel_models.py
│   │   ├── config/
│   │   │   └── test_base_config.py
│   │   └── utils/
│   │       └── test_wait_utils.py
│   ├── rpa/
│   │   └── browser/
│   │       └── test_browser_service.py
│   ├── task_manager/
│   │   ├── test_controllers.py
│   │   └── test_models.py
│   ├── integration/
│   └── e2e/
```

## 2. 测试文件命名规范

### 命名规则
1. 所有测试文件以 `test_` 开头
2. 测试文件名使用小写字母和下划线分隔
3. 测试文件名应清晰描述被测试的模块或功能
4. 禁止使用 `test_XXX_fixed.py`、`test_XXX_v2.py` 等版本后缀

### 命名示例
- ✅ 正确: `test_user_authentication.py`
- ✅ 正确: `test_data_processing.py`
- ❌ 错误: `test_user_auth_fixed.py`
- ❌ 错误: `test_data_processing_v2.py`

## 3. 测试分类组织方式

### 单元测试 (Unit Tests)
- 位置: 与源代码对应的测试目录中
- 目的: 测试单个函数、类或模块的功能
- 特点: 运行速度快，依赖少，隔离性好

### 集成测试 (Integration Tests)
- 位置: `tests/integration/` 目录
- 目的: 测试多个模块之间的交互和集成
- 特点: 涉及多个组件，可能需要外部依赖

### 端到端测试 (End-to-End Tests)
- 位置: `tests/e2e/` 目录
- 目的: 测试完整的业务流程和用户场景
- 特点: 模拟真实用户操作，运行时间较长

## 4. 测试文件重组和迁移步骤

### 迁移步骤
1. 分析现有测试文件，确定其对应的源代码模块
2. 创建目标测试目录（如不存在）
3. 将测试文件移动到对应的目录
4. 重命名不符合规范的测试文件
5. 更新测试文件中的导入路径
6. 验证所有测试仍能正常运行

### 迁移示例
```
迁移前:
tests/
├── test_models_enums.py
├── test_config_user.py
└── test_wait_utils.py

迁移后:
tests/
├── common/
│   ├── models/
│   │   └── test_enums.py
│   ├── config/
│   │   └── test_user.py
│   └── utils/
│       └── test_wait_utils.py
```

## 5. 跨平台兼容性测试规范

### 测试环境
- Windows 10/11
- macOS (最新稳定版)
- Ubuntu 20.04 LTS

### 测试内容
1. 文件路径处理兼容性
2. 编码格式兼容性
3. 命令行工具兼容性
4. 浏览器自动化兼容性

### 实施方式
- 使用 GitHub Actions 进行多平台 CI 测试
- 在测试矩阵中包含不同操作系统
- 使用 Docker 容器进行环境隔离测试

## 6. 测试执行和验证标准

### 执行标准
1. 所有单元测试必须通过
2. 代码覆盖率不低于 80%
3. 集成测试在 CI 环境中执行
4. 端到端测试定期执行

### 验证标准
1. 测试结果必须可重现
2. 测试失败必须提供详细错误信息
3. 测试执行时间需要监控和优化
4. 测试日志需要清晰可读

## 7. OpenSpec规范条文

### 测试组织规范
```
# Testing Organization Specification

## Overview
This specification defines the testing organization, structure, and practices for the AI Product Selector project.

## Requirements

### Requirement: Test Directory Structure Mapping
The test directory structure SHALL mirror the source code directory structure with a one-to-one correspondence between source modules and test modules.

#### Scenario: Source code module mapping
- WHEN a source module exists at `common/models/`
- THEN its corresponding test module SHALL exist at `tests/common/models/`

#### Scenario: CLI module mapping
- WHEN a source module exists at `cli/main.py`
- THEN its corresponding test module SHALL exist at `tests/cli/test_main.py`

### Requirement: Test File Naming Convention
Test files SHALL follow strict naming conventions to ensure consistency and avoid version proliferation.

#### Scenario: Unit test naming
- WHEN creating a unit test for `common/models/enums.py`
- THEN the test file SHALL be named `test_enums.py`

#### Scenario: Integration test naming
- WHEN creating an integration test for store processing functionality
- THEN the test file SHALL be named `test_store_processing_integration.py`

#### Scenario: End-to-end test naming
- WHEN creating an end-to-end test for the complete workflow
- THEN the test file SHALL be named `test_end_to_end_workflow.py`

#### Scenario: Invalid naming patterns
- WHEN a test file is named with suffixes like `_fixed.py`, `_v2.py`, or `_backup.py`
- THEN it SHALL be considered non-compliant and require renaming

### Requirement: Test Categorization Structure
Tests SHALL be categorized into three distinct types: Unit Tests, Integration Tests, and End-to-End Tests, each with specific organizational requirements.

#### Scenario: Unit test organization
- WHEN creating unit tests for individual functions or classes
- THEN they SHALL be placed in the corresponding module directory
- AND SHALL focus on testing a single unit in isolation
- AND SHALL not require external dependencies or services

#### Scenario: Integration test organization
- WHEN creating integration tests that verify interactions between modules
- THEN they SHALL be placed in `tests/integration/` directory
- AND MAY require mock or stub implementations for external services
- AND SHALL verify data flow and interface contracts between components

#### Scenario: End-to-end test organization
- WHEN creating end-to-end tests that verify complete user workflows
- THEN they SHALL be placed in `tests/e2e/` directory
- AND SHALL test the complete system as a user would interact with it
- AND MAY require external services or databases to be available

### Requirement: Cross-Platform Compatibility Testing
The testing framework SHALL support execution across Windows, macOS, and Linux platforms.

#### Scenario: Platform-specific test execution
- WHEN running tests on different operating systems
- THEN all tests SHALL execute without modification
- AND platform-specific functionality SHALL be tested on each supported platform

#### Scenario: Browser compatibility testing
- WHEN testing browser automation functionality
- THEN tests SHALL be executed against Chrome, Edge, and Firefox
- AND headless and non-headless modes SHALL be supported

### Requirement: Test Execution and Validation Standards
Test execution SHALL follow standardized procedures with clear validation criteria.

#### Scenario: Test execution with coverage requirements
- WHEN running the test suite
- THEN code coverage SHALL be measured
- AND core business modules SHALL achieve ≥ 80% coverage
- AND critical paths SHALL achieve 100% coverage

#### Scenario: Test result validation
- WHEN tests complete execution
- THEN results SHALL be reported in standardized format
- AND failures SHALL include detailed error information
- AND execution time SHALL be recorded for performance monitoring
