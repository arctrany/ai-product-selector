# Change: Add Item Shelf Days to User Input Data

## Why
The current system needs to filter products based on their shelf time (how long they've been listed), but this parameter is not explicitly defined in the user input data structure. Adding this attribute will allow users to specify the maximum shelf time for product selection, improving the precision of the selection process.

## What Changes
- Add `item_shelf_days` attribute to user input data structure， default value 120
- Update configuration processing to handle the new parameter
- Modify product filtering logic to consider shelf time

## Impact
- Affected specs: cli input data handling
- Affected code: cli/models.py, cli/main.py, good_store_selector.py
- Backward compatibility: maintained through default values