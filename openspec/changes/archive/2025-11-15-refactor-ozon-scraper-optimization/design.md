## Context
The `OzonScraper` class contains several redundant wrapper methods that simply call core methods without adding any value. These methods create unnecessary code duplication and maintenance overhead.

## Goals / Non-Goals
**Goals:**
- Remove redundant wrapper methods that don't add value
- Simplify the codebase while maintaining exact same functionality
- Maintain 100% backward compatibility with existing public APIs

**Non-Goals:**
- Changing public method signatures or return types
- Performance optimizations or thread safety improvements
- Adding new features or capabilities
- Modifying integration with other scrapers or services

## Decisions

### Decision 1: Remove Image Extraction Wrappers
**What**: Remove `_extract_product_image_from_content_sync()` and `_extract_product_image_from_content()` methods
**Why**: Both methods simply call `_extract_product_image()` without adding any logic
**Alternatives considered**: 
- Keep wrappers for consistency → Rejected as they serve no purpose

### Decision 2: Remove Price Extraction Wrapper
**What**: Remove `_extract_price_data_from_content_sync()` method
**Why**: Method only creates BeautifulSoup and calls `_extract_basic_data_core()` - this can be done directly
**Alternatives considered**:
- Keep wrapper for abstraction → Rejected as abstraction adds no value here

### Decision 3: Remove Unused Parameters
**What**: Remove `is_async` parameter from `_extract_basic_data_core()`
**Why**: Parameter is not used anywhere in the method logic
**Alternatives considered**:
- Keep parameter for future use → Rejected following YAGNI principle

## Risks / Trade-offs

**Risk**: Removing methods might break internal callers
→ **Mitigation**: Careful analysis of all method usage before removal

**Risk**: Future code might expect these wrapper methods to exist
→ **Mitigation**: This is private API, so no external dependencies expected

## Migration Plan

### Phase 1: Remove Wrapper Methods (1 day)
1. Remove `_extract_product_image_from_content_sync()` method
2. Remove `_extract_product_image_from_content()` method  
3. Remove `_extract_price_data_from_content_sync()` method
4. Update callers to use core methods directly
5. Remove unused `is_async` parameter

### Phase 2: Testing (1 day)
1. Run existing test suite
2. Verify functionality unchanged

### Rollback Plan
- Simple git revert if any issues discovered
- All changes are in single file, easy to rollback

## Open Questions
None - this is a straightforward code cleanup.
