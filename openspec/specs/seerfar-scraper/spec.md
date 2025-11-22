# seerfar-scraper Specification

## Purpose
TBD - created by archiving change add-seerfar-product-fields. Update Purpose after archive.
## Requirements
### Requirement: Extract Product Category
The system SHALL extract category information from Seerfar product list table rows.

#### Scenario: Category extraction success
- **WHEN** a product row contains category information in the third `<td>` element
- **THEN** the system extracts both Chinese and Russian category names
- **AND** stores them in `category_cn` and `category_ru` fields

#### Scenario: Category extraction failure
- **WHEN** category information is not available or cannot be parsed
- **THEN** the system returns `None` for both category fields
- **AND** logs a warning message

### Requirement: Extract Listing Date
The system SHALL extract listing date and shelf days from Seerfar product list table rows.

#### Scenario: Listing date extraction success
- **WHEN** a product row contains listing date in the last `<td>` element
- **THEN** the system extracts the date string (e.g., "2025-06-20")
- **AND** extracts the shelf duration (e.g., "4 个月")
- **AND** stores them in `listing_date` and `shelf_duration` fields

#### Scenario: Listing date extraction failure
- **WHEN** listing date information is not available or cannot be parsed
- **THEN** the system returns `None` for both date fields
- **AND** logs a warning message

### Requirement: Extract Sales Volume
The system SHALL extract sales volume from Seerfar product list table rows.

#### Scenario: Sales volume extraction success
- **WHEN** a product row contains sales volume in the fifth `<td>` element
- **THEN** the system extracts the numeric value
- **AND** stores it in `sales_volume` field as an integer

#### Scenario: Sales volume extraction failure
- **WHEN** sales volume information is not available or cannot be parsed
- **THEN** the system returns `None` for the sales volume field
- **AND** logs a warning message

### Requirement: No Default Values
The system SHALL NOT use hardcoded default values when data extraction fails.

#### Scenario: Failed extraction returns None
- **WHEN** any field extraction fails
- **THEN** the system returns `None` for that field
- **AND** does NOT substitute with default values like 0, "", or placeholder strings

### Requirement: Pre-filter Products Based on Extracted Fields
The system SHALL support pre-filtering products based on category, listing date, and sales volume before processing OZON detail pages.

#### Scenario: Filter function validates product eligibility
- **WHEN** a filter function is provided to `scrape_store_products()`
- **AND** basic fields (category, listing_date, sales_volume) are extracted
- **THEN** the system applies the filter function to the product data
- **AND** skips OZON detail page processing if filter returns `False`
- **AND** logs the reason for skipping

#### Scenario: Category blacklist filtering
- **WHEN** filter function checks category against a blacklist
- **AND** product category matches any blacklist keyword
- **THEN** the filter returns `False`
- **AND** the product is skipped

#### Scenario: Listing date threshold filtering
- **WHEN** filter function checks listing date
- **AND** product shelf duration exceeds the threshold
- **THEN** the filter returns `False`
- **AND** the product is skipped

#### Scenario: Sales volume filtering
- **WHEN** filter function checks sales volume
- **AND** sales volume is `None` or 0
- **THEN** the filter returns `False`
- **AND** the product is skipped

#### Scenario: Combined filter conditions
- **WHEN** filter function applies multiple conditions
- **THEN** product must satisfy ALL conditions to pass
- **AND** failing any condition results in skipping the product

### Requirement: Extract Product Weight
The system SHALL extract product weight from Seerfar product list table rows.

#### Scenario: Weight extraction success
- **WHEN** a product row contains weight in the second-to-last `<td>` element
- **THEN** the system extracts the numeric value and unit (e.g., "161 g")
- **AND** stores it in `weight` field as a float (in grams)

#### Scenario: Weight extraction failure
- **WHEN** weight information is not available or cannot be parsed
- **THEN** the system returns `None` for the weight field
- **AND** logs a warning message

### Requirement: Implement Filter Function with User Data
The system SHALL provide a filter function that validates products against user-defined criteria from `--data` parameter.

#### Scenario: Filter based on category blacklist
- **WHEN** user provides category blacklist keywords
- **AND** product category contains any blacklist keyword
- **THEN** the filter returns `False`

#### Scenario: Filter based on listing date threshold
- **WHEN** user provides `item_shelf_days` threshold
- **AND** product shelf duration exceeds the threshold
- **THEN** the filter returns `False`

#### Scenario: Filter based on sales volume range
- **WHEN** user provides `max_monthly_sold` and `monthly_sold_min` range
- **AND** product sales volume is outside the range
- **THEN** the filter returns `False`

#### Scenario: Filter based on weight range
- **WHEN** user provides `item_min_weight` and `item_max_weight` range
- **AND** product weight is outside the range
- **THEN** the filter returns `False`

#### Scenario: All filter conditions must pass
- **WHEN** multiple filter conditions are defined
- **THEN** product must satisfy ALL conditions
- **AND** failing any single condition results in filtering out the product

