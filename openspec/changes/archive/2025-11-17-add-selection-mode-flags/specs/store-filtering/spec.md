# store-filtering Spec Delta

## Added Requirements

### Requirement: Conditional Store Filtering Based on Selection Mode
The system SHALL conditionally execute store filtering based on the selection mode specified by CLI flags.

#### Scenario: Select goods mode - skip store filtering
- **WHEN** the system operates in select-goods mode (`--select-goods`)
- **THEN** store-level filtering (sales/orders validation) SHALL be skipped

#### Scenario: Select goods mode - read store IDs from Excel
- **WHEN** the system operates in select-goods mode
- **THEN** store IDs SHALL be read from the first column of the input Excel file
- **AND** only numeric values SHALL be treated as valid store IDs
- **AND** non-numeric rows SHALL be skipped

#### Scenario: Select goods mode - apply product filtering
- **WHEN** the system operates in select-goods mode
- **THEN** product-level filtering (category, weight, sales volume, shelf time) SHALL still be applied

#### Scenario: Select shops mode - current behavior
- **WHEN** the system operates in select-shops mode (`--select-shops` or default)
- **THEN** store filtering SHALL be executed as per current implementation
- **AND** store expansion/fission SHALL be performed

#### Scenario: Both modes produce consistent output format
- **WHEN** products are selected in either mode
- **THEN** the output Excel file SHALL match the template format (`docs/goods.xlsx`)
