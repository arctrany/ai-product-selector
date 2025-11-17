# Change: Add Store Filter Support

## Why
The current system needs to filter stores based on sales data during the scraping process, but this filtering logic is currently implemented internally within the Seerfar scraper. To improve modularity and reusability, we need to extract this filtering logic into a separate function in the StoreEvaluator class and allow the scrape_store_sales_data() method to accept this filter function as a parameter.

## What Changes
- Add a `filter_store()` method to the StoreEvaluator class
- Modify `scrape_store_sales_data()` method in SeerfarScraper to accept a filter function parameter
- Replace internal filtering implementation with the new external filter function

## Impact
- Affected specs: store-filtering capability
- Affected code: common/business/store_evaluator.py, common/scrapers/seerfar_scraper.py
- Backward compatibility: maintained through default values