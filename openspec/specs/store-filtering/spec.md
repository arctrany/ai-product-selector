# store-filtering Specification

## Purpose
TBD - created by archiving change add-store-filter. Update Purpose after archive.
## Requirements
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

### Requirement: Store Sales Data Scraping with Filter
The system SHALL support passing a filter function to the store sales data scraping process.

#### Scenario: Filter function provided
- **WHEN** a filter function is provided to scrape_store_sales_data()
- **THEN** the function is used to filter stores before returning results

#### Scenario: No filter function provided
- **WHEN** no filter function is provided to scrape_store_sales_data()
- **THEN** the scraping proceeds without filtering

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

