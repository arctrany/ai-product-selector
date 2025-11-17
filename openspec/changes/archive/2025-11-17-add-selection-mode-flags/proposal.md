# Change Proposal: Add Selection Mode Flags

## Overview
Add two mutually exclusive command-line flags (`--select-goods` and `--select-shops`) to support different product selection workflows.

## Motivation
Currently, the system only supports one workflow: filtering and expanding seed stores, then selecting products from qualified stores. However, users sometimes already have a curated list of stores and want to skip store filtering, directly selecting products from those stores.

## Proposed Changes

### 1. CLI Enhancement
Add two mutually exclusive flags:
- `--select-goods`: Skip store filtering, directly select products from provided store list
- `--select-shops`: Current implementation with store filtering and expansion (default)

### 2. Workflow Modes

#### Mode 1: Select Goods (`--select-goods`)
- **Input**: Excel file with store IDs (first column, numeric values only)
- **Process**:
  - Read store IDs from Excel (skip non-numeric rows)
  - Skip store-level filtering (no sales/orders validation)
  - Scrape products from each store
  - Apply product-level filtering (category blacklist, weight, sales volume, shelf time)
  - Calculate profit and similarity as usual
- **Output**: `goods.xlsx` (same format as template)

#### Mode 2: Select Shops (`--select-shops`, default)
- **Input**: Excel file with seed stores + store sales/orders data in `--data` parameter
- **Process**: Current implementation
  - Filter seed stores by sales/orders criteria
  - Expand to related stores
  - Select products from qualified stores
- **Output**: `good_shops.xlsx` and `goods.xlsx`

### 3. Implementation Approach
Use **Approach A** (simple): Add mode detection in `good_store_selector.py` to avoid complex refactoring.

## Affected Capabilities
- `cli`: Add new command-line flags
- `store-filtering`: Conditional execution based on mode

## Validation Criteria
- [ ] Two flags are mutually exclusive
- [ ] `--select-goods` mode skips store filtering
- [ ] `--select-goods` mode reads store IDs from Excel first column
- [ ] Product filtering still applies in both modes
- [ ] Output format matches template in both modes
- [ ] Works with `--dryrun` flag

## Risks and Mitigations
- **Risk**: Breaking existing workflows
  - **Mitigation**: Default to `--select-shops` mode (current behavior)
- **Risk**: Confusion about which mode to use
  - **Mitigation**: Clear error message when both flags provided; document use cases

## Related Issues
None
