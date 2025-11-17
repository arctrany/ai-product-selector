# Change: Remove Redundant Methods in OzonScraper

## Why
The current `OzonScraper` implementation contains redundant wrapper methods that simply call core methods without adding value. This creates unnecessary code duplication and maintenance overhead.

## What Changes
- **Remove redundant image extraction wrappers**: Eliminate `_extract_product_image_from_content_sync()` and `_extract_product_image_from_content()` methods
- **Remove redundant price extraction wrapper**: Eliminate `_extract_price_data_from_content_sync()` method
- **Simplify method calls**: Update callers to use core methods directly
- **Clean up unused parameters**: Remove `is_async` parameter from `_extract_price_data_core()`

## Impact
- Affected specs: ozon-scraper
- Affected code: `common/scrapers/ozon_scraper.py`
- **BREAKING**: None - all public interfaces remain unchanged
- Maintainability: Cleaner, more readable code with ~30 lines removed
- Simplicity: Fewer methods to maintain and understand
