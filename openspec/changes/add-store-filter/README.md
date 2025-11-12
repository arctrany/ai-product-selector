# Add Store Filter Support

## Summary
This change adds support for filtering stores based on sales data during the scraping process. The filtering logic has been extracted from the internal implementation of the Seerfar scraper into a separate function in the StoreEvaluator class, allowing for better modularity and reusability.

## Changes Made

### 1. Store Evaluator Updates
- Added `filter_store()` method to the StoreEvaluator class
- Implemented filtering logic based on 30-day sales amount and order count

### 2. Seerfar Scraper Updates
- Modified `scrape_store_sales_data()` method to accept a filter function parameter
- Replaced internal filtering implementation with external filter function

### 3. Testing
- Created `tests/test_store_filter.py` to verify the store filtering functionality
- All tests passed successfully

## Configuration
The store filtering uses the following default thresholds from the configuration:
- Minimum 30-day sales amount: 500,000 RUB
- Minimum 30-day order count: 250 orders

These values can be customized in the configuration file.

## Usage
The `scrape_store_sales_data()` method now accepts an optional `filter_func` parameter:

```python
from common.business.store_evaluator import StoreEvaluator

# Create store evaluator
store_evaluator = StoreEvaluator()

# Scrape store data with filtering
result = seerfar_scraper.scrape_store_sales_data("store_id", store_evaluator.filter_store)
```

If the store data doesn't meet the filtering criteria, the method will return a ScrapingResult with `success=False` and an appropriate error message.

## Impact
- Backward compatibility is maintained - existing code without the filter function will continue to work
- No breaking changes to existing functionality
- Enhanced store filtering capabilities with better modularity