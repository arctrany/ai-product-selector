## ADDED Requirements

### Requirement: Store Filter Configuration in User Data
The system SHALL accept store filtering thresholds as configurable parameters in user input data.

#### Scenario: User provides store filter thresholds
- **WHEN** user provides `min_store_sales_30days` and `min_store_orders_30days` in the `--data` JSON file
- **THEN** the system uses these values for store-level filtering in select-shops mode

#### Scenario: User omits store filter thresholds
- **WHEN** user does not provide store filter fields in the `--data` JSON file
- **THEN** the system uses default values (500,000 RUB for sales, 250 for orders)

#### Scenario: Invalid store filter values provided
- **WHEN** user provides negative or non-numeric values for store filter fields
- **THEN** the system rejects the configuration with a clear error message

#### Scenario: Store filters applied in select-shops mode
- **WHEN** running in `--select-shops` mode with user-provided store filter values
- **THEN** stores are filtered using the user-specified thresholds before product selection

#### Scenario: Store filters ignored in select-goods mode
- **WHEN** running in `--select-goods` mode
- **THEN** store filter thresholds are not applied (store filtering is skipped)
