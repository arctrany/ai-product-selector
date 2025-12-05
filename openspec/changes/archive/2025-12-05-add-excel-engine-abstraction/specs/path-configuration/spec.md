# Path Configuration Specification

## Implementation Status: BROKEN (0% - Needs complete redesign)

### Critical Issues
1. **Fallback hardcoded path**: Bypasses security validation
2. **YAML/Code mismatch**: Configuration disconnected from implementation
3. **No dynamic configuration**: Calculator paths locked in code
4. **Overly broad allowed directories**: Not sufficiently restricted
5. **Configuration layer confusion**: Three separate sources not integrated

## ADDED Requirements

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

## Current Implementation Analysis

### Architecture Overview
```
Three-layer path resolution (inconsistent):

Layer 1: paths.py (SecurePathConfig)
  ├── CALCULATOR_MAP: {'default': 'profits_calculator.xlsx', ...}
  ├── ALLOWED_DIRS: ['/app/data/calculators/', '../../docs/', ...]
  └── get_calculator_path(identifier) → Path

Layer 2: excel_engine_config.py (EngineConfig)
  ├── DEFAULT_CONFIG['paths']['calculator_identifier']: 'default'
  ├── get_calculator_path() → calls path_config.get_calculator_path()
  └── from_file(path) → NOT IMPLEMENTED

Layer 3: engine_config.yaml (ignored)
  ├── paths.calculator_directory: docs
  ├── paths.default_calculator: profits_calculator.xlsx
  └── [These are never used by code]

Layer 4: engine_factory.py (fallback bypass)
  └── Line 117: Path("docs/profits_calculator.xlsx") [hardcoded, bypasses everything]
```

### Problem Details

#### Problem 1: Fallback Hardcoded Path (URGENT)
**Location**: `common/excel_engine/engine_factory.py:116-117`

```python
else:
    # SECURITY ISSUE: Hardcoded relative path bypasses SecurePathConfig!
    calculator_path = Path("docs/profits_calculator.xlsx")
```

**Why it's a problem**:
- Fallback path is not validated through SecurePathConfig
- Relative path behavior depends on current working directory
- If config loading fails, security validation is skipped
- Inconsistent with secure path design goals

**Current impact**:
- `_create_xlwings_engine()` uses fallback when config is None
- `_create_formulas_engine()` uses fallback when config is None
- Both bypass security validation

**Test evidence**:
```python
# This should fail but doesn't:
factory = EngineFactory()
engine = factory.create_engine(None)  # Succeeds with fallback!
```

#### Problem 2: YAML Configuration Unused (HIGH)
**Location**: `common/config/engine_config.yaml`

```yaml
paths:
  calculator_directory: docs               # IGNORED
  default_calculator: profits_calculator.xlsx  # IGNORED
  compiled_rules_directory: common/excel_engine/compiled  # IGNORED
```

**Why it's a problem**:
- These fields are defined but never read by code
- Code uses hardcoded CALCULATOR_MAP in paths.py
- YAML and code configurations are out of sync
- Changes to YAML don't affect runtime behavior

**Example of mismatch**:
```python
# YAML says:
paths.default_calculator: profits_calculator.xlsx

# But code has:
CALCULATOR_MAP = {
    'default': 'profits_calculator.xlsx',
    'test': 'test_calculator.xlsx',
    'v4': '利润表V4版本.xlsx'  # YAML doesn't know about this!
}
```

#### Problem 3: Limited Dynamic Configuration (HIGH)
**Current capability**:
```python
# Can only switch between pre-mapped identifiers:
CALCULATOR_IDENTIFIER=default  # ✅ Works
CALCULATOR_IDENTIFIER=test     # ✅ Works
CALCULATOR_IDENTIFIER=/tmp/my_calculator.xlsx  # ❌ Doesn't work
CALCULATOR_IDENTIFIER=new_v4   # ❌ Doesn't work (not in CALCULATOR_MAP)
```

**Why it's a problem**:
- Cannot add new calculator paths without code changes
- No support for different calculator versions per deployment
- Cannot load calculators from external locations easily
- Operations team cannot manage calculator versions

#### Problem 4: Overly Broad Allowed Directories (MEDIUM)
**Current**:
```python
ALLOWED_DIRS = [
    '/app/data/calculators/',
    '/opt/ai-product-selector/calculators/',
    '../../docs/',      # Entire docs/ directory!
    '../../tests/resources/',  # Entire tests/ directory!
]
```

**Why it's a problem**:
- Any file in `docs/` is allowed, not just calculator files
- Any file in `tests/resources/` is allowed
- Should only allow specific filenames

**Better approach**:
```python
ALLOWED_FILES = {
    'default': '/app/data/calculators/profits_calculator.xlsx',
    'test': '/app/data/calculators/test_calculator.xlsx',
    'v4': '/app/data/calculators/利润表V4版本.xlsx',
}
```

#### Problem 5: Configuration Layer Confusion (MEDIUM)
**Three separate configuration sources**:
1. `paths.py`: CALCULATOR_MAP dict (source of truth?)
2. `engine_config.yaml`: paths.calculator_directory, etc. (ignored)
3. Environment variables: CALCULATOR_IDENTIFIER, ENGINE_DEFAULT, etc. (partial)

**No clear precedence**:
```python
# What wins in this scenario?
# YAML: default_calculator: v4_calculator.xlsx
# Env: CALCULATOR_IDENTIFIER=test
# Code: CALCULATOR_MAP['default'] = 'profits_calculator.xlsx'
```

**Difficult to understand behavior**:
```python
# Developer sees this in YAML:
# paths.default_calculator: profits_calculator.xlsx

# But code actually uses this:
identifier = self.config['paths']['calculator_identifier']  # from DEFAULT_CONFIG
path = path_config.get_calculator_path(identifier)  # uses CALCULATOR_MAP
```

## Required Implementation Changes

### Tier 1: Security Fixes (URGENT)

#### 1.1 Remove Fallback Hardcoded Path
```python
# ❌ Current (engine_factory.py:117)
else:
    calculator_path = Path("docs/profits_calculator.xlsx")

# ✅ Correct approach
else:
    raise EngineError(
        "Calculator path not configured. "
        "Configure calculator_identifier in EngineConfig or "
        "set CALCULATOR_IDENTIFIER environment variable."
    )
```

#### 1.2 Ensure All Paths Use SecurePathConfig
```python
# ❌ Current
calculator_path = Path("docs/profits_calculator.xlsx")

# ✅ Correct
calculator_path = config.get_calculator_path()  # Always goes through SecurePathConfig
```

#### 1.3 Explicit Error on Security Validation Failure
```python
# ✅ Change paths.py to fail explicitly
def get_calculator_path(self, identifier: str) -> Path:
    # ... search logic ...
    raise ValueError(f"Calculator '{identifier}' not found in allowed directories")
    # Don't fall back to other paths
```

### Tier 2: Configuration Consistency (HIGH)

#### 2.1 Choose Configuration Source
**Option A**: YAML as source of truth
```yaml
# engine_config.yaml
calculators:
  default:
    filename: profits_calculator.xlsx
    allowed_dirs:
      - /app/data/calculators
      - /opt/ai-product-selector/calculators
  test:
    filename: test_calculator.xlsx
  v4:
    filename: 利润表V4版本.xlsx
```

**Option B**: Code as source of truth
```python
# paths.py - Document why code is used
CALCULATOR_MAP = {
    'default': 'profits_calculator.xlsx',
    'test': 'test_calculator.xlsx',
    'v4': '利润表V4版本.xlsx',
}
# Keep engine_config.yaml for other settings only
```

#### 2.2 Remove Unused Configuration
If choosing Option B:
```yaml
# Remove from engine_config.yaml
paths:
  # DELETE: calculator_directory
  # DELETE: default_calculator
  # DELETE: compiled_rules_directory

  # KEEP: Only used fields
  calculator_identifier: default
  compiled_rules_path: common/excel_engine/compiled_rules.py
```

### Tier 3: Dynamic Configuration (MEDIUM)

#### 3.1 Support YAML Calculator Configuration
```python
# excel_engine_config.py
@classmethod
def from_file(cls, config_path: str) -> 'EngineConfig':
    """Load configuration from YAML file"""
    with open(config_path) as f:
        data = yaml.safe_load(f)

    # Load calculator mappings from YAML
    if 'calculators' in data:
        SecurePathConfig.CALCULATOR_MAP = data['calculators']

    return cls(config_path)
```

#### 3.2 Support Environment Variable Paths
```python
# excel_engine_config.py
def _apply_env_overrides(self, config: Dict) -> Dict:
    # Existing overrides...

    # NEW: Support calculator paths from file
    if 'CALCULATOR_CONFIG_PATH' in os.environ:
        path = os.environ['CALCULATOR_CONFIG_PATH']
        with open(path) as f:
            calculators = yaml.safe_load(f)
        SecurePathConfig.CALCULATOR_MAP.update(calculators)

    return config
```

### Tier 4: Improved Path Validation (MEDIUM)

#### 4.1 Whitelist Specific Files
```python
# paths.py - Better approach
ALLOWED_CALCULATORS = {
    'default': {
        'filename': 'profits_calculator.xlsx',
        'paths': [
            '/app/data/calculators/profits_calculator.xlsx',
            '/opt/ai-product-selector/calculators/profits_calculator.xlsx',
        ]
    },
    'test': {
        'filename': 'test_calculator.xlsx',
        'paths': ['/app/data/calculators/test_calculator.xlsx']
    }
}

def get_calculator_path(self, identifier: str) -> Path:
    allowed = ALLOWED_CALCULATORS.get(identifier)
    if not allowed:
        raise ValueError(f"Unknown calculator: {identifier}")

    for allowed_path in allowed['paths']:
        path = Path(allowed_path)
        if path.exists():
            return path

    raise ValueError(f"Calculator '{identifier}' not found")
```

## Migration Path

### Phase 1: Fix Immediate Security Issue (30 minutes)
1. Remove fallback hardcoded path from engine_factory.py
2. Make missing config raise explicit error
3. Ensure all paths go through SecurePathConfig

### Phase 2: Synchronize Configuration (1 hour)
1. Choose YAML or code as source of truth
2. Remove unused configuration
3. Document configuration precedence

### Phase 3: Enable Dynamic Configuration (2 hours)
1. Implement EngineConfig.from_file() method
2. Add CALCULATOR_CONFIG_PATH environment variable support
3. Add tests for configuration loading

### Phase 4: Improve Path Validation (1 hour)
1. Change ALLOWED_DIRS to ALLOWED_CALCULATORS
2. Whitelist specific files instead of directories
3. Update tests

## Rollback Plan
- Configuration changes are backwards compatible
- Can revert to code-based CALCULATOR_MAP if YAML fails
- Fallback removal requires test updates but no breaking changes
