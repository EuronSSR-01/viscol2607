# Evidence and state notes

- `confidence` may be `null` when the downstream model did not supply a number. Non-vision agents must not invent scores.
- Distinguish `trusted_facts`, `inferred`, `not_visible`, and `uncertain`.
- States: `UNCONFIGURED` → `AWAITING_UPLOAD_CONFIRMATION` → `IN_PROGRESS` → `SUCCEEDED` | `FAILED` | `STOPPED_UNCERTAIN`.
- Default budgets: MAX_VISUAL_CALLS=8, MAX_PROVIDER_ATTEMPTS=2, MAX_REPAIR_ROUNDS=4.
