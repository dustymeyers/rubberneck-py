# Active Work Queue

Keep this file tactical. Detailed product intent and completion requirements
belong in `ROADMAP.md`.

## Next: Full-Text Rules Search

### Design

- [ ] Define tokenization and normalization rules for search queries.
- [ ] Define title, exact-phrase, all-term, and partial-term ranking weights.
- [ ] Define excerpt length and match-context behavior.
- [ ] Decide the minimum useful query length and maximum result count.

### Implementation

- [ ] Load full descriptions for every catalog entry into a local search index.
- [ ] Add `/rules search <text>` without changing `/rules lookup` semantics.
- [ ] Rank title matches ahead of description-only matches.
- [ ] Generate concise excerpts around matching text.
- [ ] Emphasize matches without corrupting existing Markdown.
- [ ] Paginate search results in a single Discord response.
- [ ] Handle empty, short, and no-result queries with useful guidance.

### Verification

- [ ] Add ranking and exact-phrase tests.
- [ ] Add excerpt-boundary and highlighting tests.
- [ ] Add result-limit and no-result tests.
- [ ] Confirm search performs no network requests after indexing completes.
- [ ] Manually verify `/rules search attack while hidden` in Discord.
- [ ] Confirm every acceptance criterion in Roadmap Feature Block 2.

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

## Maintenance Backlog

- [ ] Modernize the legacy bestiary cog using the generic async API client.
- [ ] Make Redis optional for every command, not only `/rule`.
- [ ] Remove or isolate the paginator demonstration cog from production startup.
- [ ] Add formatting and linting configuration.
- [ ] Decide whether runtime and development dependencies should be separated.
- [ ] Review the legacy root layout and choose a proper application package
  structure.
