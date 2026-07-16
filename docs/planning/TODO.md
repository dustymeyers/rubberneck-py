# Active Work Queue

Keep this file tactical. Detailed product intent and completion requirements
belong in `ROADMAP.md`.

## Next: Unified Rules, Conditions, and Definitions

### Design

- [ ] Inventory the SRD endpoints suitable for short reference lookups.
- [ ] Decide which resource types belong in the first unified lookup release.
- [ ] Define a common reference model for title, index, type, description, and
  source URL.
- [ ] Define exact, prefix, and substring ranking behavior.
- [ ] Decide how `/rule` communicates its migration to `/rules lookup`.

### Implementation

- [ ] Create the `/rules` slash-command group.
- [ ] Generalize resource loading across selected endpoints.
- [ ] Add conditions to lookup and autocomplete.
- [ ] Build a combined, precomputed autocomplete index.
- [ ] Add type labels to suggestions and responses.
- [ ] Generalize Markdown normalization across description shapes.
- [ ] Preserve `/rule` as a compatibility alias.

### Verification

- [ ] Add unit tests for the common reference model.
- [ ] Add lookup-ranking tests.
- [ ] Add ambiguity and duplicate-name tests.
- [ ] Add condition-formatting tests.
- [ ] Add command-level tests for explicit and unified lookup paths.
- [ ] Manually verify autocomplete and response rendering in Discord.
- [ ] Confirm every acceptance criterion in Roadmap Feature Block 1.

## Maintenance Backlog

- [ ] Modernize the legacy bestiary cog using the generic async API client.
- [ ] Make Redis optional for every command, not only `/rule`.
- [ ] Remove or isolate the paginator demonstration cog from production startup.
- [ ] Add formatting and linting configuration.
- [ ] Decide whether runtime and development dependencies should be separated.
- [ ] Review the legacy root layout and choose a proper application package
  structure.
