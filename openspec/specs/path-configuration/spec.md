# path-configuration Specification

## Purpose
TBD - created by archiving change add-excel-engine-abstraction. Update Purpose after archive.
## Requirements
### Requirement: Unified Calculator Path Configuration
The system SHALL provide a single, consistent configuration system for calculator file paths that prevents security bypass and supports operational flexibility.

#### Scenario: Secure path resolution through configuration
- **GIVEN** engine initialization without direct path parameter
- **WHEN** EngineFactory requests calculator path
- **THEN** EngineConfig resolves path through SecurePathConfig using validated identifier

#### Scenario: Configuration consistency
- **GIVEN** YAML configuration specifying calculator paths
- **WHEN** EngineFactory creates engine
- **THEN** YAML configuration is actually used (not hardcoded fallbacks)

#### Scenario: No fallback bypass
- **GIVEN** engine configuration unavailable or invalid
- **WHEN** EngineFactory creates engine
- **THEN** it raises explicit error, does not silently fallback to hardcoded path

### Requirement: Dynamic Calculator Configuration
The system SHALL support adding new calculator identifiers and paths without code changes.

#### Scenario: Environment variable configuration
- **GIVEN** environment variable `CALCULATOR_PATHS_YAML=/etc/app/calculators.yaml`
- **WHEN** configuration system initializes
- **THEN** it loads calculator mappings from that file

#### Scenario: Runtime calculator registration
- **GIVEN** an application running in production
- **WHEN** a new calculator version is added to configuration
- **THEN** the application can use it without restart

### Requirement: Restrictive Path Validation
The system SHALL limit file access to only authorized calculator files, not entire directories.

#### Scenario: Specific file whitelist
- **GIVEN** configuration lists specific allowed calculator files
- **WHEN** path validation checks a file
- **THEN** it only allows files explicitly listed, not any file in directory

#### Scenario: Path traversal prevention
- **GIVEN** a path like `../../../etc/passwd` is requested
- **WHEN** validation runs
- **THEN** the path is rejected with clear error message

