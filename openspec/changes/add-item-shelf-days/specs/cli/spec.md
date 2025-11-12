## ADDED Requirements
### Requirement: Item Shelf Days Configuration
The system SHALL accept item shelf days as a configurable parameter in user input data.

#### Scenario: Valid shelf days provided
- **WHEN** user provides item_created_days parameter in input data
- **THEN** the system uses this value for shelf time filtering

#### Scenario: Default shelf days used
- **WHEN** user does not provide item_created_days parameter in input data
- **THEN** the system uses a default value of 150 days for shelf time filtering