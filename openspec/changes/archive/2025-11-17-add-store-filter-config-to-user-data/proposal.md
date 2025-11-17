# Change: Add Store Filter Configuration to User Data

## Why
Currently, store filtering thresholds (min_sales_30days and min_orders_30days) are hardcoded in the system configuration with default values (500,000 RUB and 250 orders). Users cannot customize these critical filtering criteria through the `--data` parameter, which is the primary way users configure the application. This creates an inconsistency where product-level filters are user-configurable but store-level filters are not.

## What Changes
- Add `min_store_sales_30days` and `min_store_orders_30days` fields to the `--data` JSON file format
- Update `UIConfig` dataclass to include these new fields
- Modify `load_user_data()` in `cli/main.py` to read these fields from user data
- Apply user-provided store filter values to `GoodStoreSelectorConfig.store_filter` in `handle_start_command()`
- Update CLI help text and documentation to reflect the new fields
- Add validation to ensure values are positive numbers

## Impact
- **Affected specs**: `cli`, `store-filtering`
- **Affected code**: 
  - `cli/models.py` (UIConfig dataclass)
  - `cli/main.py` (load_user_data, handle_start_command)
  - User data JSON files (new optional fields)
- **Backward compatibility**: Fully backward compatible - new fields are optional with sensible defaults
- **User benefit**: Users can now customize store filtering thresholds without modifying system configuration files
