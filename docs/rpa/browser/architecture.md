## RPA Browser Architecture

- Package: `src_new/rpa/browser`
- Modules:
  - `config.py`: configuration management, directories, backend selection
  - `errors.py`: error hierarchy
  - `driver_factory.py`: backend driver creation (playwright/selenium)
  - `browser_service.py`: resource-safe automation API (initialize, open_page, screenshot)
- Cross-platform, configuration-driven, no hard-coded paths
- Designed for extensibility and SOLID principles