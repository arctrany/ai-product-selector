## MODIFIED Requirements

### Requirement: Mode flags work with dryrun
The system SHALL execute in the specified mode with enhanced dry-run behavior that reports filtering decisions without actually filtering data.

#### Scenario: Dryrun mode with store filtering
- **WHEN** user provides `--dryrun` flag in select-shops mode
- **THEN** the system SHALL execute store filtering logic
- **AND** SHALL log detailed filtering decisions for each store (pass/fail, reasons, threshold comparisons)
- **AND** SHALL NOT actually filter out any stores (all stores are processed)
- **AND** SHALL mark log entries with "🧪 [DRYRUN]" prefix

#### Scenario: Dryrun mode with product filtering
- **WHEN** user provides `--dryrun` flag in either mode
- **THEN** the system SHALL execute product filtering logic
- **AND** SHALL log detailed filtering decisions for each product (pass/fail, reasons, threshold comparisons)
- **AND** SHALL NOT actually filter out any products (all products are processed)
- **AND** SHALL mark log entries with "🧪 [DRYRUN]" prefix

#### Scenario: Dryrun mode filtering report format
- **WHEN** running in dryrun mode
- **THEN** each filtering decision SHALL include:
  - Item identifier (store ID or product index)
  - Overall result (PASS or FILTERED)
  - List of filter conditions checked
  - For each failed condition: field name, actual value, threshold value, comparison operator
  - Summary statistics at the end (total checked, would pass, would be filtered)

#### Scenario: Dryrun mode does not save results
- **WHEN** user provides `--dryrun` flag
- **THEN** the system SHALL NOT save results to output files
- **AND** SHALL log a message indicating dryrun mode is active
- **AND** SHALL process all data as if no filtering was applied

#### Scenario: Normal mode filtering behavior unchanged
- **WHEN** user does NOT provide `--dryrun` flag
- **THEN** filtering SHALL work as before (actually filter out items)
- **AND** SHALL NOT log detailed filtering reports
- **AND** SHALL save results to output files
