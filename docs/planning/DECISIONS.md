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
