# Active Work Queue

Keep this file tactical. Detailed product intent and completion requirements
belong in `ROADMAP.md`.

Feature Block 4 is complete. Its implementation record and intentionally
deferred candidates are preserved in `DIARY.md`, `DECISIONS.md`, and
`ROADMAP.md`.

## Feature Block 5: Searchable Bestiary and Random Encounter Foundation

### 1. Generalize Catalog Navigation

- [ ] Define shared result-summary and detail-page presenter contracts.
- [ ] Generalize the existing reference navigator around registered presenters
  without weakening its tested state/history behavior.
- [ ] Preserve exact Back/Forward snapshots, pagination, interaction ownership,
  timeout handling, and public/private responses.
- [ ] Add shared contract tests before moving monster commands onto it.

### 2. Build the Monster Catalog

- [ ] Normalize API payloads into typed monster records with explicit
  provenance.
- [ ] Normalize challenge ratings, including fractional values, and expose
  reusable type, size, alignment, environment, and CR metadata.
- [ ] Load and index monsters once at startup with no API call per search or
  autocomplete interaction.
- [ ] Handle missing and version-dependent fields without losing usable
  monsters.

### 3. Add Monster Browse and Search

- [ ] Move `/monsters` onto numbered result selection with full stat blocks in
  the same message.
- [ ] Add local monster search with deterministic ordering and reusable filters.
- [ ] Preserve filters, result page, selected monster, and stat-block page
  across navigation history.
- [ ] Keep `/monster` as the direct exact-name shortcut with consistent
  visibility and errors.

### 4. Add Generator-Ready Selection

- [ ] Provide deterministic seeded random selection over the same filtered
  monster catalog.
- [ ] Separate reusable encounter-selection services from Discord presentation.
- [ ] Add extension points for related spells, items, environments, and future
  encounter-generator actions.
- [ ] Cover empty catalogs, impossible filters, API failures, and no-result
  searches with useful responses.

### 5. Block Closeout

- [ ] Test normalization, fractional CR values, filtering, ordering,
  pagination, multi-step history, ownership, visibility, provenance, and seeded
  selection.
- [ ] Perform focused Discord integration checks for public and private monster
  browse/search/navigation.
- [ ] Run the full pytest, Ruff, formatting, and clean-diff checks.
- [ ] Update planning records and prepare the next-block handoff.
- [ ] Review the complete branch diff before publishing.
