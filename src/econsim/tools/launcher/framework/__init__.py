"""
Manual Test Framework - Core infrastructure for eliminating test duplication.

This framework extracts common patterns from the 7 manual tests to provide:
- Configuration-driven test definitions
- Standardized 3-panel UI (debug | viewport | controls)  
- 6-phase transition management
- Centralized debug logging orchestration
- Simulation factory with deterministic seeding

Reduces new test creation from ~400 lines to ~30 lines.
"""