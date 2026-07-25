# Active Work Queue

Keep this file tactical. Detailed product intent and completion requirements
belong in `ROADMAP.md`.

## Feature Block 4: Reference Quality-of-Life

### 1. Close the Autocomplete Measurement Loop

- [x] Benchmark representative exact, prefix, substring, empty, and no-result
  queries against the warm local index.
- [x] Record index construction time and estimated memory for both references
  and monsters.
- [ ] Manually measure the visible Discord autocomplete delay separately from
  local callback execution.
- [ ] Document the observed client debounce/network limitation and reconcile
  the corresponding roadmap acceptance criteria.

### 2. Add Shared Response Visibility

- [x] Define one optional `private`/ephemeral parameter with a consistent,
  unsurprising public default.
- [x] Centralize defer/respond visibility behavior so lookup, search, list, and
  compatibility commands do not implement it independently.
- [x] Ensure interactive navigation remains usable within Discord's ephemeral
  response and component-timeout limits.
- [x] Test public defaults, private responses, deferred followups, and error
  responses.

### 3. Add Stable Source Links

- [ ] Verify which upstream 2014 SRD URLs are stable and useful to a person,
  rather than linking blindly to raw or version-ambiguous endpoints.
- [ ] Add source-link construction to shared reference presentation code.
- [ ] Make the link available from every lookup/search-navigation path without
  adding noisy duplicate fields.
- [ ] Test URL construction, missing URLs, and source/version labeling.

### 4. Add Browsable Rule Listings

- [ ] Finalize `/rules list [topic]` semantics using the currently supported
  rule and condition categories.
- [ ] Build list results from the warm local catalog with deterministic
  ordering and no per-command API request.
- [ ] Reuse the existing one-message paginator and result-to-reference
  navigation.
- [ ] Provide useful empty-topic, empty-catalog, and invalid-topic responses.
- [ ] Test filtering, ordering, pagination, result selection, back/forward
  navigation, interaction ownership, and private visibility.

### 5. Block Closeout

- [ ] Run the full pytest, Ruff, formatting, and clean-diff checks.
- [ ] Perform Discord integration checks for list navigation, source links,
  visibility, and autocomplete latency.
- [ ] Update the roadmap, decision log, diary, and this queue with completed
  scope and intentionally deferred candidates.
- [ ] Review the complete branch diff before publishing.

### Deferred Candidates

- `/rules compare`
- `/rules random`
- Persistent server/user visibility and SRD-version preferences

These remain roadmap candidates but are not part of the current Block 4 scope.
