## ADDED Requirements

### Requirement: Code Structure Simplification
The OzonScraper SHALL maintain clean, non-redundant code structure by eliminating unnecessary wrapper methods that do not add functional value.

#### Scenario: Image extraction methods consolidation
- **WHEN** extracting product images from page content
- **THEN** the system SHALL use the core extraction method directly without redundant wrapper methods
- **AND** maintain identical functionality and return values

#### Scenario: Price data extraction methods consolidation  
- **WHEN** extracting price data from page content
- **THEN** the system SHALL use the core extraction method directly without redundant wrapper methods
- **AND** maintain identical functionality and return values

#### Scenario: Method parameter cleanup
- **WHEN** calling core extraction methods
- **THEN** the system SHALL not pass unused parameters
- **AND** maintain method signature compatibility where needed
