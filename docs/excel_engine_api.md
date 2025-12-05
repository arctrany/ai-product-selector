# Excel Engine API Reference

## Quick Start

```python
from common.business.excel_calculator import ExcelProfitCalculator
from common.models import ProfitCalculatorInput

# Create calculator (auto-selects best engine)
calculator = ExcelProfitCalculator()

# Prepare input
input_data = ProfitCalculatorInput(
    black_price=120.0,
    green_price=100.0,
    list_price=95.0,
    purchase_price=50.0,
    commission_rate=10.0,
    weight=500.0,
    length=10.0,
    width=10.0,
    height=10.0
)

# Calculate profit
result = calculator.calculate_profit(input_data)
print(f"Profit: {result.profit_amount}, Rate: {result.profit_rate}%")
```

## Engine Selection

```python
# Use specific engine
calculator = ExcelProfitCalculator({"engine": {"default": "python"}})

# Available engines:
# - "auto": Automatic selection based on platform
# - "python": Pre-compiled rules (fastest, cross-platform)
# - "xlwings": Direct Excel (Windows/Mac only, 100% accurate)
# - "formulas": Formula parser (cross-platform, moderate speed)
```

## Batch Processing

```python
# Process multiple items efficiently
inputs = [input1, input2, input3, ...]
results = calculator.batch_calculate(inputs)
```

## Configuration

```yaml
# engine_config.yaml
engine:
  default: auto
  cache_enabled: true

performance:
  batch_size: 100
  timeout: 30
```

Or via environment:
```bash
export EXCEL_ENGINE_DEFAULT=python
export EXCEL_ENGINE_LOG_LEVEL=INFO
```

## Validation Mode

```python
from common.excel_engine.validation_engine import ValidationEngine

# Compare results across engines
validator = ValidationEngine(
    primary_engine="xlwings",
    comparison_engines=["python"],
    tolerance=0.01  # 1%
)

result = validator.calculate_profit(input_data)
if not result.log_info['validation']['is_valid']:
    print("Validation failed:", result.log_info['validation']['discrepancies'])
```