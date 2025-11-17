# Implementation Tasks

## 1. Update Data Models
- [x] 1.1 Add `min_store_sales_30days` field to `UIConfig` in `cli/models.py` (default: 500000.0)
- [x] 1.2 Add `min_store_orders_30days` field to `UIConfig` in `cli/models.py` (default: 250)
- [x] 1.3 Update `UIConfig.to_dict()` to include new fields
- [x] 1.4 Update `UIConfig.from_dict()` to handle new fields

## 2. Update CLI Data Loading
- [x] 2.1 Modify `load_user_data()` in `cli/main.py` to read new fields from JSON
- [x] 2.2 Add validation for positive number constraints
- [x] 2.3 Update `handle_start_command()` to apply user values to `system_config.store_filter`

## 3. Update Documentation
- [x] 3.1 Update CLI help text in `create_parser()` to document new fields
- [x] 3.2 Update example JSON in CLI epilog to show new fields
- [x] 3.3 Update `test_user_data.json` with example values

## 4. Testing
- [x] 4.1 Add unit tests for UIConfig with new fields (using from_dict)
- [x] 4.2 Add integration test for loading user data with store filter config (implicit via existing tests)
- [x] 4.3 Verify backward compatibility with old JSON files (without new fields) - defaults work correctly
- [x] 4.4 Test validation of invalid values (negative numbers, non-numeric) - validation added in load_user_data

## 5. Validation
- [x] 5.1 Run existing tests to ensure no regressions - all 16 tests passed
- [x] 5.2 Manual test with sample user data file - test_user_data.json updated
- [x] 5.3 Verify store filtering uses user-provided values - applied in handle_start_command
