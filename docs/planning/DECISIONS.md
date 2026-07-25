# Decision Log

This is an append-only summary of decisions that affect future implementation.
If a decision changes, add a new entry that supersedes the old one rather than
silently rewriting history.

## 2026-07-16 — Build Vertical Slices

**Decision:** Modernize one complete user-facing path at a time, beginning with
rules lookup, rather than rewriting the whole legacy bot first.

**Reason:** A vertical slice validates Discord interaction behavior, API access,
caching, formatting, and tests while delivering immediate value.

## 2026-07-16 — Async API Access with Optional Caching

**Decision:** New commands use the generic asynchronous `DnDAPI` client and must
not require Redis. Process-local TTL caching is the current default.

**Reason:** Blocking HTTP calls stall the Discord event loop, and a local Redis
server should not be required for basic development or deployment.

## 2026-07-16 — Pytest for Automated Tests

**Decision:** Use pytest and pytest-asyncio rather than unittest-style test
classes and assertions.

**Reason:** Pytest syntax is the project preference and provides concise async
test support.

## 2026-07-16 — Constants for Meaningful Values

**Decision:** Repeated or domain-significant values use named constants,
including endpoints, timeouts, limits, reusable messages, and footer text.
One-off local prose may remain inline when a constant would obscure context.

**Reason:** Meaningful values should be discoverable and changeable without
searching through implementation details.

## 2026-07-16 — Optimize for Readability, Not Platform Maximums

**Decision:** Rule pages target a normal Discord viewport and split by document
structure. Headings stay with their first paragraph.

**Reason:** Discord's technical embed limit produces cards that are too large to
scan comfortably during play.

## 2026-07-16 — Precompute Autocomplete

**Decision:** Autocomplete is served from a precomputed in-memory index. It must
not perform network requests or runtime full-list filtering per keystroke.

**Reason:** Discord autocomplete is latency-sensitive and already includes
client/network debounce outside the bot's control.

## 2026-07-16 — Unified Reference Catalog

**Decision:** Rule sections and conditions are exposed through one typed catalog.
Autocomplete values encode the resource type, while labels show it to the user.
Additional reference endpoints are added through `ReferenceType` configuration.

**Reason:** Users should not need to know which upstream API endpoint owns a
term, and duplicate names must remain unambiguous without adding API clients.

## 2026-07-16 — One Unified Lookup Command

**Decision:** Expose `/rules lookup` as the only typed reference subcommand.
Keep `/rule` temporarily as a compatibility alias, but do not add separate
`/rules rule` and `/rules condition` commands.

**Reason:** Typed autocomplete already identifies each result. Separate commands
duplicate the unified lookup and require users to understand API categories.

## 2026-07-23 — Deterministic Local Full-Text Search

**Decision:** `/rules search` uses a local, immutable index of every reference
title and fully loaded description. `/rules lookup` keeps its existing
title-based resolution semantics.

Queries and indexed text use Unicode NFKC normalization, case folding, and
collapsed whitespace. Words are sequences of Unicode letters or numbers;
punctuation, underscores, and hyphens are token boundaries. Repeated query
terms are discarded for term scoring while their original order remains
significant for full-phrase matching. Markdown syntax is excluded from indexed
text so formatting characters do not create matches.

Eligible results must match the normalized full phrase or every distinct query
term. A term matches an entire token first and may otherwise match a token
prefix; arbitrary within-word substring matching is not used. Results receive
these additive weights:

- exact normalized title: 2,000
- full query phrase in the title: 1,000
- every query term matched in the title: 500
- each exact title term: 100
- each title-prefix term: 50
- full query phrase in the description: 400
- every query term matched in the description: 200
- each exact description term: 20
- each description-prefix term: 10

Ties sort by normalized title, resource type, and resource index so results are
stable. A term is scored only by its best match in each field.

Each result shows an excerpt of at most 300 visible characters. The excerpt is
centered on the highest-value description match, prefers complete sentence or
paragraph boundaries when they fit, and uses ellipses when either edge is
trimmed. If only the title matches, the excerpt begins with the description's
first complete sentence. Matching is computed on plain text; emphasis is added
after excerpt selection by escaping existing Discord Markdown and then wrapping
matched spans in bold markers.

After trimming, a query must contain at least three visible characters and at
least one token of two or more characters. Search returns at most 20 results,
with five results per paginator page. Empty and shorter queries receive guidance
instead of running a search.

**Reason:** A small SRD corpus favors transparent, testable ranking over a
database search dependency. Requiring all terms keeps results relevant, prefix
matching tolerates remembered word endings, and bounded excerpts and result
pages remain readable during play.

## 2026-07-24 — One Stateful Reference Navigator

**Decision:** Feature Block 3 uses one custom `discord.ui.View` to render search
results, full references, and later related references in the same message. It
does not compose or replace multiple Pycord `Paginator` instances.

Search mode displays one string-select menu containing the five results on the
current page. A second component row contains previous, page indicator, next,
and back controls. This remains below Discord's limits of five component rows,
25 components per view, and 25 options per string select. Reference mode reuses
the same page controls, disables result selection, and enables back navigation.

Navigation state records the original query, immutable ranked results, search
page, current reference and reference page, and a history stack. State changes
are serialized with an async lock. Back restores the complete prior snapshot,
including its page, instead of recomputing a default view.

The full source name and description loaded for search indexing are retained in
the local index. Opening a search result uses that indexed content and the
existing reference formatter without another API request.

Related entries will live in a separate typed relationship table keyed by
catalog value. Relationships are explicitly ordered, deterministic, and
validated against the loaded catalog. Missing targets are omitted. Presentation
code consumes the resulting entries but does not own relationship data.

Only the user who invoked the command may operate its controls. Other users
receive private guidance. Controls time out after the existing five-minute
interaction window and are disabled on the message. Repeated or concurrent
clicks are serialized so an older callback cannot overwrite newer state.

**Reason:** A single state owner makes forward and back behavior testable,
preserves page context, avoids extra channel messages, and leaves enough
component capacity for related-reference selection without coupling navigation
to Pycord paginator internals.
