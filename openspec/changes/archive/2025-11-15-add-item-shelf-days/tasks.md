## 1. Data Model Updates
- [x] 1.1 Add item_shelf_days field to UIConfig dataclass
- [x] 1.2 Update UIConfig.from_dict method to handle new field
- [x] 1.3 Update UIConfig.to_dict method to include new field

## 2. CLI Interface Updates
- [x] 2.1 Update command line argument parser to accept shelf days parameter
- [x] 2.2 Update help documentation with new parameter description
- [x] 2.3 Update example configuration files

## 3. Business Logic Integration
- [x] 3.1 Modify product filtering logic to consider shelf time
- [x] 3.2 Update configuration processing to handle new parameter
- [x] 3.3 Add validation for shelf days parameter

## 4. Testing
- [x] 4.1 Add unit tests for new data model field
- [x] 4.2 Add integration tests for CLI parameter handling
- [x] 4.3 Update existing tests to handle new parameter