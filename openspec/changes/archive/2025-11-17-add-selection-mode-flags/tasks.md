# Tasks for add-selection-mode-flags

## Task 1: Add CLI flags for selection modes
**Status**: completed
**Capability**: cli

Add two mutually exclusive command-line flags:
- `--select-goods`: Skip store filtering, directly select products from provided store list
- `--select-shops`: Current implementation with store filtering (default)

**Acceptance Criteria**:
- Two flags are mutually exclusive (error if both provided)
- Default behavior is `--select-shops` when neither flag is specified
- Flags work with existing `--dryrun` flag
- Clear error message when both flags are provided

**Files to modify**:
- `main.py`: Add argument parsing for new flags

## Task 2: Implement select-goods mode in good_store_selector
**Status**: completed
**Capability**: store-filtering

Modify `good_store_selector.py` to support two modes:
1. **Select Goods Mode** (`--select-goods`):
   - Read store IDs from Excel first column (numeric values only)
   - Skip store-level filtering (no sales/orders validation)
   - Scrape products from each store
   - Apply product-level filtering
   - Calculate profit and similarity
   - Output `goods.xlsx`

2. **Select Shops Mode** (`--select-shops`, default):
   - Current implementation unchanged

**Acceptance Criteria**:
- Mode detection based on CLI flag
- Select-goods mode reads store IDs from Excel correctly
- Select-goods mode skips store filtering
- Product filtering applies in both modes
- Output format matches template in both modes

**Files to modify**:
- `good_store_selector.py`: Add mode detection and conditional logic

## Task 3: Add tests for selection mode logic
**Status**: completed
**Capability**: testing

Add unit tests to verify the selection mode functionality works correctly.

**Acceptance Criteria**:
- Test CLI flag parsing (mutual exclusivity, default behavior)
- Test select-goods mode: Excel reading, store ID extraction
- Test select-shops mode: default behavior unchanged
- Test mode detection in GoodStoreSelector
- Test that product filtering applies in both modes
- Mock external dependencies (scrapers, Excel files)

**Files to create/modify**:
- `tests/test_selection_modes.py`: New test file for mode logic
- `tests/test_cli_flags.py`: Test CLI argument parsing

## Task 4: Update documentation
**Status**: pending
**Capability**: cli

Update user-facing documentation to explain the two modes.

**Acceptance Criteria**:
- README or user guide explains when to use each mode
- Examples provided for both modes

**Files to modify**:
- `README.md` or relevant documentation files
