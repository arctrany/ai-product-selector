# Excel Engine Specification

## Implementation Status: IN PROGRESS (75%)

### ✅ 已修复的阻塞性问题 (2025-12-05)

| 问题 | 状态 | 位置 |
|------|------|------|
| XlwingsEngine 单元格映射 | ✅ 已修复 | `xlwings_engine.py:134-172` |
| 安全测试 | ✅ 8/8 通过 | `test_security_path_config.py` |
| 安全 fallback 绕过 | ✅ 已修复 | `engine_factory.py:115-121` |

### ⚠️ 待完善问题 (非阻塞)

| 问题 | 优先级 | 位置 |
|------|--------|------|
| 运费计算逻辑只有 10% | HIGH | `compiled_rules.py` |
| EngineConfig.from_file() 未实现 | LOW | `excel_engine_config.py` |

### Component Status
- **Architecture**: 80% ✅ Protocol 定义良好
- **Security/Path Management**: 90% ✅ 8/8 测试通过
- **ExcelCompiler**: 20% ⚠️ 生成代码不可用 (可延后)
- **PythonEngine**: 60% ⚠️ 可运行但运费逻辑简化
- **XlwingsEngine**: 85% ✅ **单元格映射已修复**
- **Configuration**: 70% ⚠️ from_file() 未实现
- **Testing**: 75% ✅ 核心测试通过

## ADDED Requirements

### Requirement: Secure Calculator Path Management
The system SHALL manage calculator file paths through secure system configuration instead of accepting them as CLI parameters to prevent unauthorized access to file system paths.

#### Scenario: CLI parameter rejection
- **GIVEN** a user attempts to pass calculator file path as CLI parameter
- **WHEN** the CLI processes the arguments
- **THEN** the system rejects the parameter and displays an error message about using system configuration

#### Scenario: Secure path resolution
- **GIVEN** a calculator identifier "default" in the configuration
- **WHEN** the system needs to access the calculator file
- **THEN** it resolves the path through SecurePathConfig with validation against allowed directories

#### Scenario: Path traversal prevention
- **GIVEN** a malicious path attempt like "../../sensitive/file.xlsx"
- **WHEN** the path validation runs
- **THEN** the system rejects the path and logs a security warning

### Requirement: Calculation Engine Interface
The system SHALL provide an abstract interface for profit calculation engines that supports multiple implementations including Excel-based and Python-based calculations.

#### Scenario: Engine initialization with auto-detection
- **GIVEN** a profit calculator is initialized without specifying an engine
- **WHEN** the system detects the environment
- **THEN** it automatically selects the best available engine (xlwings on Windows/Mac with Excel, Python otherwise)

#### Scenario: Fallback to alternative engine
- **GIVEN** xlwings engine is requested but Excel is not available
- **WHEN** the engine fails to initialize
- **THEN** the system falls back to the next available engine in the configured order

### Requirement: XlWings Excel Engine
The system SHALL provide an xlwings-based calculation engine that uses actual Excel files for 100% accurate profit calculations including complex shipping lookup tables.

#### Scenario: Calculate profit with shipping costs
- **GIVEN** an Excel file with shipping rate tables
- **WHEN** calculating profit for a product with weight 450g, dimensions 30x30x30cm, price 331 RMB
- **THEN** the engine returns the exact profit matching Excel's calculation including volumetric weight and shipping channel selection

#### Scenario: Excel formula dependency resolution
- **GIVEN** Excel formulas that reference multiple sheets (UNI运费, 运费方式, 利润计算表)
- **WHEN** input values are updated
- **THEN** all dependent formulas are recalculated automatically

### Requirement: Python Calculation Engine with Pre-compilation
The system SHALL provide a pre-compiled Python implementation that replicates Excel calculations with 100% accuracy through compile-time extraction of Excel logic.

#### Scenario: Excel compilation process
- **GIVEN** an Excel profit calculator file with formulas and lookup tables
- **WHEN** running the Excel compiler tool
- **THEN** it generates Python code containing all shipping rules, formulas, and calculation logic

#### Scenario: Pre-compiled rule execution
- **GIVEN** Python engine with pre-compiled rules
- **WHEN** calculating profit for a product
- **THEN** the result matches Excel calculation exactly using the compiled lookup tables and formulas

#### Scenario: Compilation validation
- **GIVEN** newly compiled Python rules from Excel
- **WHEN** running validation tests
- **THEN** all test cases produce identical results between Excel and compiled Python code

### Requirement: Engine Validation Mode
The system SHALL support a validation mode that compares results across different engines to ensure calculation accuracy.

#### Scenario: Cross-engine validation
- **GIVEN** validation mode is enabled
- **WHEN** a profit calculation is requested
- **THEN** the system runs the calculation on multiple engines and logs any discrepancies

#### Scenario: Validation report generation
- **GIVEN** a batch of calculations completed in validation mode
- **WHEN** requesting a validation report
- **THEN** the system provides statistics on calculation differences between engines

### Requirement: Engine Performance Optimization
The system SHALL optimize engine performance through caching, connection pooling, and batch operations.

#### Scenario: Excel instance reuse
- **GIVEN** xlwings engine is initialized
- **WHEN** multiple calculations are performed
- **THEN** the same Excel instance is reused, reducing startup overhead

#### Scenario: Batch calculation optimization
- **GIVEN** a request to calculate profits for 100 products
- **WHEN** using xlwings engine
- **THEN** the engine performs batch updates to Excel, minimizing COM calls

### Requirement: Engine Configuration Management
The system SHALL provide configuration options to control engine selection, performance settings, and validation behavior.

#### Scenario: Engine selection via configuration
- **GIVEN** configuration specifies "engine": "xlwings"
- **WHEN** initializing the calculator
- **THEN** the xlwings engine is used regardless of auto-detection

#### Scenario: Performance tuning settings
- **GIVEN** configuration with "cache_enabled": true, "batch_size": 50
- **WHEN** processing multiple calculations
- **THEN** results are cached and operations are batched according to settings

## IMPLEMENTATION ISSUES (2025-12-05 Review)

### ✅ Issue 1: XlwingsEngine 单元格映射 - 已修复
**Status**: FIXED | **Location**: `xlwings_engine.py:134-172`

**修复内容**:
- 利润计算表 Sheet: A4←weight, A5←length, A6←width, A7←height, A11←list_price, B11←purchase_price
- UNI运费 Sheet: M3-M8 完整映射，包括 M8 送货方式参数
- 输出读取: G11←profit, C11←shipping_cost, E11←commission

**Excel 结构参考**:
```
利润计算表 Sheet:
  A4: 重量(g) ← weight
  A5: 长(cm) ← length
  A6: 宽(cm) ← width
  A7: 高(cm) ← height
  A11: 定价 ← list_price
  B11: 采购成本 ← purchase_price
  G11: =A11-B11-C11-D11-E11-F11 ← 利润

UNI运费 Sheet (M列):
  M3: 重量(g)
  M4: 长(cm)
  M5: 宽(cm)
  M6: 高(cm)
  M7: 销售价格(卢布)
  M8: 送货方式 ("自提点"/"送货上门")
```

### ⚠️ Issue 2: 运费计算逻辑不完整 (非阻塞)
**Severity**: HIGH (但非阻塞) | **Location**: `compiled_rules.py`

**当前实现**: 只有 10 个固定费率档位

**实际 Excel 逻辑**:
- 6 个物流渠道 (K8, K15, K22, K29, K36, K43)
- 每个渠道有复杂条件: 尺寸限制、重量范围、价格范围
- 送货方式区分: 自提点 vs 送货上门
- 公式: `=IF(AND(MAX($M$4:$M$6)<=V, SUM($M$4:$M$6)<=U, ...), IF($M$8="自提点", Y+M3*Z, AA+M3*AB), "")`

### ✅ Issue 3: 安全测试 - 已修复
**Status**: FIXED | **Location**: `test_security_path_config.py`, `paths.py`

**修复内容**:
- `validate_path()` 现在正确抛出 `ConfigurationError`
- `get_calculator_path()` 使用 `ConfigurationError` 而非 `ValueError`
- 添加了文件扩展名验证 (只允许 .xlsx, .xls, .xlsm)
- 8/8 测试全部通过

### ✅ Issue 4: 安全 Fallback 绕过 - 已修复
**Status**: FIXED | **Location**: `engine_factory.py:115-121`

**修复内容**:
- 移除了硬编码的 fallback 路径
- 现在需要显式配置 calculator_identifier
- 未配置时抛出 EngineError 提示配置方法

### ⚠️ LOW: Configuration Issues (非阻塞)
- `EngineConfig.from_file()` 未实现 - 可延后
- YAML 配置与代码需同步 - 可延后