# excel-engine Specification

## Purpose
TBD - created by archiving change add-excel-engine-abstraction. Update Purpose after archive.
## Requirements
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

