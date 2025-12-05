# Excel Calculation Engine System

## Overview

The Excel calculation engine system provides a flexible, high-performance solution for profit calculations. It supports multiple calculation engines with automatic selection based on platform and requirements.

## Features

- **Multiple Engines**: Python (pre-compiled), xlwings (Excel direct), formulas (parser)
- **Auto-Selection**: Automatically chooses the best engine for your platform
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **High Performance**: Optimized for batch processing
- **Validation Mode**: Compare results across engines
- **Security**: Path traversal protection built-in

## Quick Start

```python
from common.business.excel_calculator import ExcelProfitCalculator
from common.models import ProfitCalculatorInput

# Auto-select best engine
calculator = ExcelProfitCalculator()

# Calculate profit
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

result = calculator.calculate_profit(input_data)
print(f"Profit: ¥{result.profit_amount:.2f}")
```

## Engine Comparison

| Engine | Platform | Speed | Accuracy | Dependencies |
|--------|----------|-------|----------|--------------|
| Python | All | ★★★★★ | ★★★★☆ | None |
| xlwings | Win/Mac | ★★★☆☆ | ★★★★★ | Excel |
| formulas | All | ★★★☆☆ | ★★★★☆ | formulas lib |

## Configuration

Set default engine via environment:
```bash
export EXCEL_ENGINE_DEFAULT=python
```

Or configuration file:
```yaml
# engine_config.yaml
engine:
  default: python
  cache_enabled: true
```

## Pre-compiling Excel Rules

For best performance, pre-compile Excel files:
```bash
make compile-excel
# or
python scripts/compile_excel.py docs/profits_calculator.xlsx
```

## Validation

Ensure accuracy by comparing engines:
```python
from common.excel_engine.validation_engine import ValidationEngine

validator = ValidationEngine(
    primary_engine="xlwings",
    comparison_engines=["python"],
    tolerance=0.01
)
```

## Security

The system prevents path traversal attacks:
- Calculator files must be in approved directories
- Use identifiers instead of direct paths
- All access is logged

## Troubleshooting

See `docs/excel_engine_troubleshooting.md` for common issues.

## Architecture

```
┌─────────────────────┐
│ ExcelProfitCalculator│
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │EngineFactory│
    └──────┬──────┘
           │
    ┌──────▼────────┬────────────┬───────────┐
    │ PythonEngine  │ XlwingsEngine│ FormulasEngine│
    └───────────────┴────────────┴───────────┘
```

## Contributing

When adding new engines:
1. Implement the `CalculationEngine` protocol
2. Add to `EngineFactory`
3. Update configuration schema
4. Add tests

## License

See main project license.