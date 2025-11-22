# cli Spec Delta

## Added Requirements

### Requirement: Selection Mode Flags
The system SHALL provide two mutually exclusive command-line flags to control the selection workflow mode.

#### Scenario: Select goods mode specified
- **WHEN** user provides `--select-goods` flag
- **THEN** the system skips store filtering and directly selects products from provided store list

#### Scenario: Select shops mode specified
- **WHEN** user provides `--select-shops` flag
- **THEN** the system performs store filtering and expansion (current behavior)

#### Scenario: No mode flag specified
- **WHEN** user does not provide either mode flag
- **THEN** the system defaults to select shops mode (`--select-shops`)

#### Scenario: Both mode flags specified
- **WHEN** user provides both `--select-goods` and `--select-shops` flags
- **THEN** the system SHALL reject the command with a clear error message indicating the flags are mutually exclusive

#### Scenario: Mode flags work with dryrun
- **WHEN** user provides a mode flag along with `--dryrun`
- **THEN** the system executes in the specified mode with dry-run behavior
