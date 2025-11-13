## 1. Remove Redundant Image Extraction Methods
- [ ] 1.1 Remove `_extract_product_image_from_content_sync()` method
- [ ] 1.2 Remove `_extract_product_image_from_content()` async method
- [ ] 1.3 Update callers to use `_extract_product_image_core()` directly

## 2. Remove Redundant Price Extraction Method
- [ ] 2.1 Remove `_extract_price_data_from_content_sync()` method
- [ ] 2.2 Update `scrape_product_prices()` to call `_extract_price_data_core()` directly
- [ ] 2.3 Remove unused `is_async` parameter from `_extract_price_data_core()`

## 3. Testing and Validation
- [ ] 3.1 Run existing test suite to ensure no functionality regression
- [ ] 3.2 Verify all price extraction still works correctly
- [ ] 3.3 Verify all image extraction still works correctly
