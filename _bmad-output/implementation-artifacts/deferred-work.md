# Deferred Work

## Deferred from: Code Review of Story 1.3, 1.4, 1.5 (2026-04-04)

- **LOW: Documentation-implementation mismatch** — Story spec shows `{timestamp}_{country}_{query}.json` but implementation truncates query and applies additional escaping. Minor discrepancy, update docs in next spec revision. (From: epic-01-search-acquisition.md)

- **LOW: Timestamp precision collision** — File naming uses `strftime("%Y%m%d_%H%M%S")` (second precision). Same query run within same second overwrites previous file. Low probability, can optimize in future PR. (From: epic-01-search-acquisition.md)
