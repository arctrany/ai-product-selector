## ADR-0001: Modular RPA Browser

- Context: monolithic browser automation under `src/playweight`
- Decision: create modular package `src_new/rpa/browser`
- Consequences: clearer boundaries, testable units, safer resource lifecycle
- Status: accepted