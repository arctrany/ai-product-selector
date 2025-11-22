## MODIFIED Requirements

### Requirement: Store Filtering Function
The system SHALL provide a separate function for filtering stores based on sales data using configurable thresholds.

#### Scenario: Valid store passes filter with custom thresholds
- **WHEN** a store with sales data meeting user-configured thresholds is processed
- **THEN** the filter function returns true

#### Scenario: Invalid store fails filter with custom thresholds
- **WHEN** a store with sales data below user-configured thresholds is processed
- **THEN** the filter function returns false

#### Scenario: Filter uses default thresholds when not configured
- **WHEN** no custom thresholds are provided by the user
- **THEN** the filter uses system default values (500,000 RUB sales, 250 orders)
