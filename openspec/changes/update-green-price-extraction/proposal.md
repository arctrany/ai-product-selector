# Proposal: Update Green Price Extraction Logic

## Why
The current specification does not adequately address the scenario where green price cannot be obtained from Ozon product pages. According to the updated crawling requirements, when green price is unavailable, the system should fall back to using black price for profit calculation. This change ensures our profit calculator handles edge cases in real-world data extraction scenarios.

## What Changes
- Modify profit calculator specification to define behavior when green price is unavailable
- Update scenarios to include fallback logic using black price
- Clarify pricing strategy when only black price is available

## Impact
- Affected specs: profit-calculator
- Affected code: apps/xuanping/common/excel_calculator.py
- No breaking changes to existing interfaces