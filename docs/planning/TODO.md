# Active Work Queue

Keep this file tactical. Detailed product intent and completion requirements
belong in `ROADMAP.md`.

## Completed: Full-Text Rules Search

### Design

- [x] Define tokenization and normalization rules for search queries.
- [x] Define title, exact-phrase, all-term, and partial-term ranking weights.
- [x] Define excerpt length and match-context behavior.
- [x] Decide the minimum useful query length and maximum result count.

### Implementation

- [x] Load full descriptions for every catalog entry into a local search index.
- [x] Add `/rules search <text>` without changing `/rules lookup` semantics.
- [x] Rank title matches ahead of description-only matches.
- [x] Generate concise excerpts around matching text.
- [x] Emphasize matches without corrupting existing Markdown.
- [x] Paginate search results in a single Discord response.
- [x] Handle empty, short, and no-result queries with useful guidance.

### Verification

- [x] Add ranking and exact-phrase tests.
- [x] Add excerpt-boundary and highlighting tests.
- [x] Add result-limit and no-result tests.
- [x] Confirm search performs no network requests after indexing completes.
- [x] Manually verify `/rules search attack while hidden` in Discord.
- [x] Confirm every acceptance criterion in Roadmap Feature Block 2.

## Completed: Unified Rules, Conditions, and Definitions

### Design

- [x] Inventory the SRD endpoints suitable for short reference lookups.
- [x] Decide which resource types belong in the first unified lookup release.
- [x] Define a common reference model for title, index, type, description, and
  source URL.
- [x] Define exact, prefix, and substring ranking behavior.
- [x] Decide how `/rule` communicates its migration to `/rules lookup`.

### Implementation

- [x] Create the `/rules lookup` command.
- [x] Generalize resource loading across selected endpoints.
- [x] Add conditions to lookup and autocomplete.
- [x] Build a combined, precomputed autocomplete index.
- [x] Add type labels to suggestions and responses.
- [x] Generalize Markdown normalization across description shapes.
- [x] Preserve `/rule` as a compatibility alias.

### Verification

- [x] Add unit tests for the common reference model.
- [x] Add lookup-ranking tests.
- [x] Add ambiguity and duplicate-name tests.
- [x] Add condition-formatting tests.
- [x] Add command metadata tests for unified lookup and the compatibility alias.
- [x] Manually verify autocomplete and response rendering in Discord.
- [x] Confirm every acceptance criterion in Roadmap Feature Block 1.

## Next: Search and Related-Rule Navigation

### Design

- [ ] Choose the Discord control used to select a search result.
- [ ] Define navigation state for query, search page, selected reference, and
  reference page.
- [ ] Define how related references are stored and ranked.
- [ ] Define interaction ownership and expired-control behavior.

### Implementation

- [ ] Let a user open a full reference directly from `/rules search` results.
- [ ] Reuse lookup formatting and pagination for the selected reference.
- [ ] Add back navigation to the originating search result page.
- [ ] Keep search, reference, and related-rule navigation in one response.
- [ ] Display deterministic related rules or conditions on reference responses.
- [ ] Handle missing related resources without breaking navigation.

### Verification

- [ ] Add search-result selection and full-reference tests.
- [ ] Add forward, back, and page-state restoration tests.
- [ ] Add missing-relation, expired-control, and interaction-ownership tests.
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
