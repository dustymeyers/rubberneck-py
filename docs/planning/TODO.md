# Active Work Queue

Keep this file tactical. Detailed product intent and completion requirements
belong in `ROADMAP.md`.

## Next: Search and Related-Rule Navigation

### Design

- [x] Choose the Discord control used to select a search result.
- [x] Define navigation state for query, search page, selected reference, and
  reference page.
- [x] Map the navigation design to Discord component and row limits.
- [x] Decide whether full-reference navigation uses already indexed content or
  performs a cached API lookup.
- [x] Define how related references are stored and ranked.
- [x] Define interaction ownership and expired-control behavior.

### Implementation

- [x] Let a user open a full reference directly from `/rules search` results.
- [x] Reuse lookup formatting and pagination for the selected reference.
- [x] Add back navigation to the originating search result page.
- [x] Add forward navigation that restores the reference and page left by Back.
- [x] Keep search and selected-reference navigation in one response.
- [x] Build one navigation view that renders search and reference states without
  losing page history.
- [ ] Extend the navigation view to related-entry states without losing page
  history.
- [ ] Display deterministic related rules or conditions on reference responses.
- [ ] Handle missing related resources without breaking navigation.
- [ ] Disable or replace stale controls when the interaction expires.

### Verification

- [x] Add search-result selection and full-reference tests.
- [x] Add forward, back, and page-state restoration tests.
- [ ] Add missing-relation, expired-control, and interaction-ownership tests.
- [ ] Add concurrent-user and repeated-click interaction tests.
- [ ] Manually verify search-to-reference-to-search navigation in Discord.
- [ ] Confirm every acceptance criterion in Roadmap Feature Block 3.

## Maintenance Backlog

- [ ] Profile and optimize autocomplete callback and end-to-end latency.
- [ ] Modernize the legacy bestiary cog using the generic async API client.
- [ ] Make Redis optional for every command, not only `/rule`.
- [ ] Remove or isolate the paginator demonstration cog from production startup.
- [ ] Add formatting and linting configuration.
- [ ] Decide whether runtime and development dependencies should be separated.
- [ ] Review the legacy root layout and choose a proper application package
  structure.
