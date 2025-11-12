t## 1. Data Model Updates
- [ ] 1.1 Add item_shelf_days field to UIConfig dataclass
- [ ] 1.2 Update UIConfig.from_dict method to handle new field
- [ ] 1.3 Update UIConfig.to_dict method to include new field

## 2. CLI Interface Updates
- [ ] 2.1 Update command line argument parser to accept shelf days parameter
- [ ] 2.2 Update help documentation with new parameter description
- [ ] 2.3 Update example configuration files

## 3. Business Logic Integration
- [ ] 3.1 Modify product filtering logic to consider shelf time
- [ ] 3.2 Update configuration processing to handle new parameter
- [ ] 3.3 Add validation for shelf days parameter

## 4. Testing
- [ ] 4.1 Add unit tests for new data model field
- [ ] 4.2 Add integration tests for CLI parameter handling
- [ ] 4.3 Update existing tests to handle new parameter