# Excel Engine Configuration Guide

This guide explains how to configure the Excel calculation engine system.

## Configuration Overview

The engine system supports multiple configuration sources:
1. Default configuration (built-in)
2. Configuration files (YAML or JSON)
3. Environment variables
4. Programmatic configuration

Configuration is loaded in this order, with later sources overriding earlier ones.

## Configuration File

### Location

The system looks for configuration files in these locations (in order):
1. `./engine_config.yaml` or `./engine_config.json` (current directory)
2. `~/.excel_engine/config.yaml` (user home directory)
3. `common/config/engine_config.yaml` (project directory)

### Format

Configuration can be in YAML or JSON format. Here's an example YAML configuration:

```yaml
# engine_config.yaml
engine:
  default: auto  # auto, python, xlwings, formulas, validation
  fallback_order:
    - xlwings
    - python
    - formulas
  cache_enabled: true
  
  validation:
    enabled: false
    tolerance: 0.01  # 1% tolerance
    engines:
      - python

paths:
  calculator_directory: docs
  default_calculator: profits_calculator.xlsx

xlwings:
  visible: false
  display_alerts: false

logging:
  level: INFO
  log_calculations: false
  log_performance: true

performance:
  batch_size: 100
  timeout: 30
```

## Environment Variables

You can override configuration using environment variables:

```bash
# Engine selection
export EXCEL_ENGINE_DEFAULT=python

# Enable/disable caching
export EXCEL_ENGINE_CACHE_ENABLED=true

# Set calculator path
export EXCEL_CALCULATOR_DIR=/path/to/calculators
export EXCEL_DEFAULT_CALCULATOR=my_calculator.xlsx

# Logging level
export EXCEL_ENGINE_LOG_LEVEL=DEBUG

# Performance settings
export EXCEL_ENGINE_BATCH_SIZE=50
```

## Engine Types

### auto (default)
Automatically selects the best available engine based on platform:
- Windows/macOS: Tries xlwings first, then falls back
- Linux: Uses Python engine

### python
Uses pre-compiled Python rules for calculations:
- Cross-platform compatible
- Fastest performance
- Requires compiled rules

### xlwings
Uses Excel directly via COM automation:
- 100% accurate Excel calculations
- Windows and macOS only
- Requires Excel installed

### formulas
Uses the formulas library to parse Excel:
- Cross-platform
- Good compatibility
- Moderate performance

### validation
Special mode that runs multiple engines and compares results:
- Useful for testing and verification
- Slower performance
- Configurable tolerance

## Programmatic Configuration

### Loading Configuration

```python
from common.config.engine_config import get_engine_config, set_engine_config

# Use default configuration
config = get_engine_config()

# Load from specific file
config = EngineConfig.from_file("my_config.yaml")

# Create from dictionary
config_dict = {
    "engine": {"default": "python"},
    "logging": {"level": "DEBUG"}
}
config = EngineConfig(config_dict)

# Set as global configuration
set_engine_config(config)
```

### Using with Calculator

```python
from common.business.excel_calculator import ExcelProfitCalculator

# Use default configuration
calculator = ExcelProfitCalculator()

# Use custom configuration
config = {"engine": {"default": "xlwings"}}
calculator = ExcelProfitCalculator(engine_config=config)

# Switch engines at runtime
calculator.switch_engine("python")
```

## Validation Mode

Enable validation mode to compare results across engines:

```yaml
engine:
  validation:
    enabled: true
    tolerance: 0.01  # 1% tolerance
    engines:
      - python
      - xlwings
```

Or programmatically:

```python
from common.excel_engine.validation_engine import ValidationEngine

# Create validation engine
engine = ValidationEngine(
    primary_engine="xlwings",
    comparison_engines=["python"],
    tolerance=0.01
)

# Generate validation report
inputs = [...]  # List of inputs to test
report = engine.generate_validation_report(inputs)
print(f"Validation rate: {report['summary']['validation_rate']}%")
```

## Performance Tuning

### Batch Processing

```yaml
performance:
  batch_size: 100  # Process 100 items at once
```

### Caching

```yaml
engine:
  cache_enabled: true  # Reuse engine instances
```

### Timeouts

```yaml
performance:
  timeout: 30  # Timeout after 30 seconds
  max_retries: 3  # Retry failed calculations
```

## Security Configuration

The system includes security features to prevent path traversal:

```yaml
paths:
  calculator_directory: docs  # Restricted directory
  # Only predefined calculators can be used
```

## Logging Configuration

### Log Levels

```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_calculations: false  # Log each calculation
  log_performance: true  # Log timing information
```

### Example Log Output

```
INFO: Initialized with engine: python
INFO: Calculation complete: profit=123.45, rate=15.67%, time=0.023s, engine=python
INFO: Batch calculation complete: 100 items in 2.34s
```

## Troubleshooting

### Engine Not Found

If an engine fails to load:
1. Check platform compatibility
2. Install required dependencies
3. Check fallback configuration

### Performance Issues

1. Enable caching
2. Use batch processing
3. Consider Python engine for Linux

### Validation Failures

1. Check tolerance settings
2. Verify Excel file compatibility
3. Review calculation logs

## Best Practices

1. **Development**: Use validation mode to ensure accuracy
2. **Production**: Use Python engine for performance
3. **Testing**: Use xlwings for 100% Excel compatibility
4. **Linux**: Always use Python or formulas engine

## Configuration Schema

The complete configuration schema is available at:
`common/config/engine_config_schema.json`

Use this for validation and IDE support.