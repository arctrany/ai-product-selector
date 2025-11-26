## 1. Remove Redundant Image Extraction Methods
- [x] 1.1 Remove `_extract_product_image_from_content_sync()` method
- [x] 1.2 Remove `_extract_product_image_from_content()` async method
- [x] 1.3 Update callers to use `_extract_product_image()` directly

## 2. Remove Redundant Price Extraction Method
- [x] 2.1 Remove `_extract_price_data_from_content_sync()` method
- [x] 2.2 Update `scrape_product_basics()` to call `_extract_basic_data_core()` directly
- [x] 2.3 Remove unused `is_async` parameter from `_extract_basic_data_core()`

## 3. Testing and Validation
- [x] 3.1 Run existing test suite to ensure no functionality regression
- [x] 3.2 Verify all price extraction still works correctly
- [x] 3.3 Verify all image extraction still works correctly
