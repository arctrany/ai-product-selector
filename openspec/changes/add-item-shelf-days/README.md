# Add Item Shelf Days to User Input Data

## Summary
This change adds support for item shelf days (the number of days a product has been listed) as a configurable parameter in the user input data. This allows users to filter products based on their shelf time, improving the precision of the product selection process.

## Changes Made

### 1. Data Model Updates
- Added `item_shelf_days` field to `UIConfig` dataclass in `cli/models.py`
- Added `shelf_days` field to `ProductInfo` dataclass in `common/models.py`

### 2. CLI Interface Updates
- Updated `load_user_data` function in `cli/main.py` to handle the new `item_shelf_days` parameter
- Updated help documentation and example configuration files

### 3. Business Logic Integration
- Added shelf time validation logic in `ProfitEvaluator` class in `common/business/profit_evaluator.py`
- Products with shelf days exceeding the configured threshold will be rejected during profit evaluation

### 4. Testing
- Created `tests/test_shelf_time_filter.py` to verify the shelf time filtering functionality
- All tests passed successfully

## Configuration
The `item_shelf_days` parameter can be configured in the user data JSON file:
```json
{
  "item_shelf_days": 150
}
```

The default value is 150 days if not specified.

## Impact
- Backward compatibility is maintained through default values
- No breaking changes to existing functionality
- Enhanced product filtering capabilities