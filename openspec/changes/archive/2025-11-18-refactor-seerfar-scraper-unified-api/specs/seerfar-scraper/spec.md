# seerfar-scraper Specification Deltas

## MODIFIED Requirements

### Requirement: Unified Store Scraping Interface
The system SHALL provide a unified `scrape()` method that combines store sales data and product list scraping with filter injection support.

#### Scenario: Scrape with product filter
- **WHEN** `scrape()` is called with `store_id`, `include_products=True`, and `product_filter_func`
- **THEN** the system scrapes store sales data
- **AND** scrapes product list with the provided filter function
- **AND** returns combined result with both sales data and filtered products

#### Scenario: Scrape with store filter
- **WHEN** `scrape()` is called with `store_id` and `store_filter_func`
- **THEN** the system scrapes store sales data
- **AND** applies the store filter function to sales data
- **AND** if filter returns `False`, skips product scraping and returns early
- **AND** if filter returns `True`, continues to scrape products

#### Scenario: Scrape with both filters
- **WHEN** `scrape()` is called with both `store_filter_func` and `product_filter_func`
- **THEN** the system applies store filter first
- **AND** only proceeds to product scraping if store filter passes
- **AND** applies product filter during product scraping
- **AND** returns combined result with filtered data

#### Scenario: Scrape without filters (backward compatible)
- **WHEN** `scrape()` is called with only `store_id` and `include_products=True`
- **THEN** the system scrapes both sales data and products without filtering
- **AND** returns complete unfiltered data
- **AND** maintains backward compatibility with existing code

#### Scenario: Control maximum products
- **WHEN** `scrape()` is called with `max_products` parameter
- **THEN** the system limits product scraping to the specified number
- **AND** passes this limit to `scrape_store_products()` method

#### Scenario: Store filter rejects early
- **WHEN** `scrape()` is called with `store_filter_func` that returns `False`
- **THEN** the system returns `ScrapingResult` with `success=False`
- **AND** includes sales data in the result
- **AND** does NOT scrape products
- **AND** logs the reason for skipping

### Requirement: Filter Function Injection
The system SHALL support dependency injection of filter functions to decouple filtering logic from scraping logic.

#### Scenario: Inject product filter function
- **WHEN** a product filter function is provided to `scrape()`
- **THEN** the system passes it to `scrape_store_products()` method
- **AND** the filter is applied during product extraction
- **AND** filtered products are excluded from OZON detail page processing

#### Scenario: Inject store filter function
- **WHEN** a store filter function is provided to `scrape()`
- **THEN** the system applies it to sales data after scraping
- **AND** uses the filter result to decide whether to continue
- **AND** logs filter decisions for debugging

#### Scenario: Filter function receives correct data format
- **WHEN** store filter function is called
- **THEN** it receives sales data dictionary with keys: `sold_30days`, `sold_count_30days`, `daily_avg_sold`
- **WHEN** product filter function is called
- **THEN** it receives product data dictionary with keys: `product_category_cn`, `product_category_ru`, `product_listing_date`, `product_shelf_duration`, `product_sales_volume`, `product_weight`


