# Excel Engine Troubleshooting

## Common Issues

### Engine Not Found
```
Error: xlwings not installed
```
**Solution**: Install xlwings or use Python engine:
```bash
pip install xlwings  # For Windows/Mac
# Or use Python engine:
export EXCEL_ENGINE_DEFAULT=python
```

### Linux Compatibility
xlwings doesn't work on Linux. Use:
```python
calculator = ExcelProfitCalculator({"engine": {"default": "python"}})
```

### Performance Issues
Enable caching and batch processing:
```yaml
engine:
  cache_enabled: true
performance:
  batch_size: 100
```

### Validation Failures
Adjust tolerance if needed:
```python
validator = ValidationEngine(tolerance=0.05)  # 5% tolerance
```

## Debug Mode

```bash
export EXCEL_ENGINE_LOG_LEVEL=DEBUG
```

## Security

Calculator files are restricted to configured directories. To add new calculators:
1. Place in `docs/` directory
2. Add to `common/config/paths.py` CALCULATOR_MAP
3. Use identifier instead of path