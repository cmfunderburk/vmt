### Bilateral Trade (Phase 2 – Draft Enumeration)
A feature-flagged draft (ECONSIM_TRADE_DRAFT=1) now enumerates potential bilateral trade intents between co-located agents. This phase:
- Adds deterministic intent structures without executing trades.
- Provides a debug overlay (up to 3 intents) for visibility.
- Preserves determinism hash and performance characteristics.

No gameplay / outcome changes yet. Disable the flag (default) for zero overhead.
