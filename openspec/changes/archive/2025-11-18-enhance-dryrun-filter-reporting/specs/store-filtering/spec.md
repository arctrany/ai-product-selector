## MODIFIED Requirements

### Requirement: Store Filtering Function
The system SHALL provide a separate function for filtering stores based on sales data using configurable thresholds, with enhanced reporting in dryrun mode.

#### Scenario: Valid store passes filter with custom thresholds
- **WHEN** a store with sales data meeting user-configured thresholds is processed
- **THEN** the filter function returns true

#### Scenario: Invalid store fails filter with custom thresholds
- **WHEN** a store with sales data below user-configured thresholds is processed
- **AND** NOT in dryrun mode
- **THEN** the filter function returns false

#### Scenario: Dryrun mode - store filtering reports but does not filter
- **WHEN** a store is processed in dryrun mode
- **THEN** the filter function SHALL check all filtering conditions
- **AND** SHALL log detailed filtering decision:
  - Store identifier
  - Each condition checked (sales threshold, orders threshold)
  - Actual values vs threshold values
  - Overall result (PASS or FILTERED)
- **AND** SHALL return true (do not filter) regardless of actual filtering result
- **AND** SHALL prefix log messages with "🧪 [DRYRUN] 店铺过滤报告"

#### Scenario: Filter uses default thresholds when not configured
- **WHEN** no custom thresholds are provided by the user
- **THEN** the filter uses system default values (500,000 RUB sales, 250 orders)

## ADDED Requirements

### Requirement: Product Filtering with Dryrun Reporting
The system SHALL provide product-level filtering with detailed reporting in dryrun mode.

#### Scenario: Product passes all filters
- **WHEN** a product meets all filtering criteria
- **THEN** the filter function returns true

#### Scenario: Product fails one or more filters
- **WHEN** a product fails one or more filtering criteria
- **AND** NOT in dryrun mode
- **THEN** the filter function returns false
- **AND** logs which filter(s) failed

#### Scenario: Dryrun mode - product filtering reports but does not filter
- **WHEN** a product is processed in dryrun mode
- **THEN** the filter function SHALL check all filtering conditions:
  - Category blacklist
  - Shelf duration (listing date)
  - Sales volume range (min/max)
  - Weight range (min/max)
- **AND** SHALL log detailed filtering decision:
  - Product identifier (index or ID)
  - Each condition checked
  - Actual values vs threshold values
  - Overall result (PASS or FILTERED)
  - Specific reason if filtered (which condition failed)
- **AND** SHALL return true (do not filter) regardless of actual filtering result
- **AND** SHALL prefix log messages with "🧪 [DRYRUN] 商品过滤报告"

#### Scenario: Dryrun mode summary statistics
- **WHEN** batch processing completes in dryrun mode
- **THEN** the system SHALL log summary statistics:
  - Total stores checked
  - Stores that would pass filtering
  - Stores that would be filtered (with reason breakdown)
  - Total products checked
  - Products that would pass filtering
  - Products that would be filtered (with reason breakdown)
