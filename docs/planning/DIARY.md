# Development Diary

## 2026-07-16 — Resumed the Project

Returned to the older Rubberneck codebase. The existing project had a Pycord
bot, a monster-specific D&D API client, Redis integration, and an unfinished
bestiary cog. We chose rules lookup as the first modernized vertical slice
because it is immediately useful during play.

## 2026-07-16 — Built `/rule`

Added a generic asynchronous client for the versioned 2014 D&D 5e SRD API. The
new client uses process-local TTL caching and does not require Redis. Added the
`/rule` command with autocomplete, friendly-name normalization, Discord embeds,
error handling, and pytest coverage.

The first Discord integration test exposed a Pycord incompatibility with
deferred annotations on `discord.Option`. Removing the future-annotations import
fixed both command execution and autocomplete registration. A global application
command error handler was added so future failures produce useful logs and a
user-facing response.

## 2026-07-16 — Improved Presentation and Interaction Speed

Changed long rule responses from multiple messages to a single button-driven
paginator. Reduced page size for normal screens and replaced character-only
splitting with structure-aware pagination that keeps headings with their first
paragraph. Added SRD Markdown normalization to remove duplicate titles and
translate unsupported headings.

Autocomplete initially depended on a cold API request and later still felt slow
because Discord applies its own debounce. Rule names are now preloaded, and all
substring suggestions are precomputed so each callback is only a dictionary
lookup. Excessively verbose synchronous Discord gateway logging was reduced.

## 2026-07-16 — Established the Next Priorities

Agreed on the next reference milestones:

1. Unify rule sections, conditions, and definitions under `/rules`.
2. Add full-text search across cached SRD content.
3. Add related-rule navigation within a single response.
4. Follow with reference quality-of-life features.

Created this planning directory to preserve the roadmap, acceptance criteria,
decisions, active tasks, and development history as Rubberneck evolves.

## 2026-07-16 — Started Unified References

Started Feature Block 1 by adding a typed reference catalog over the existing
async API client. The first release combines rule sections and conditions,
ranks exact matches ahead of prefix and substring matches, and precomputes
typed autocomplete choices.

Added `/rules lookup`, `/rules rule`, and `/rules condition`. The original
`/rule` command remains as a compatibility alias and points users toward the
unified lookup. A live API smoke test loaded 48 combined references and resolved
`restrained` as a condition. Discord rendering still needs a manual integration
check before the feature block can be marked complete.

The first bot restart showed only the existing global `/rule` command even
though logs confirmed Discord accepted `/rules` as an upsert. The group now uses
the configured `GUILD_ID` for immediate development-server synchronization and
falls back to global registration when no guild is configured.

After testing both rule and condition lookups successfully in Discord, the
command surface was simplified. `/rules rule` and `/rules condition` were
removed as redundant; typed autocomplete makes `/rules lookup` sufficient.
Feature Block 1 is complete, with `/rule` retained temporarily for compatibility.

## 2026-07-23 — Designed Full-Text Rules Search

Defined the search contract before implementation: normalized Unicode word
tokens, deterministic weighted ranking, all-term eligibility with token-prefix
fallback, Markdown-safe 300-character excerpts, a three-character minimum
query, and a 20-result cap displayed five results per page. Search will use
fully loaded descriptions in a local immutable index and will not alter
`/rules lookup` behavior.

Implemented the local full-description index and `/rules search`. Results use
the documented deterministic weights, Markdown-safe contextual excerpts, and a
single paginator with five results per page. Empty, short, and no-result queries
receive private guidance. Automated coverage verifies ranking, phrase and
prefix behavior, excerpt highlighting and boundaries, result limits, stable
ties, and that searches perform no API calls after indexing.

Live Discord verification confirmed that `/rules search attack while hidden`
returns relevant indexed rules with readable highlighted excerpts. Feature
Block 2 is complete.

Identified the first concrete Feature Block 3 journey: search results should
open their full reference text directly, then return to the originating query
and result page. This extends related-rule navigation into a general
single-response reference browser instead of leaving search results as
dead-end excerpts.

Added autocomplete responsiveness to the reference quality-of-life roadmap.
Future work will measure local callback latency separately from Discord's
end-to-end delay, quantify index construction and memory costs, and optimize
only after identifying whether the bot or platform debounce is the bottleneck.

## 2026-07-24 — Designed the Reference Navigator

Feature Block 3 will use one owner-restricted custom Discord view as a state
machine for search results, full references, back history, and related entries.
The current search page supplies five select-menu options, navigation controls
share a second row, and indexed source content opens without another API
request. Concurrent state changes will be locked and expired controls disabled.
Related-entry data will remain separate, explicitly ordered, and validated
against the catalog.

Implemented the first navigation slice. Successful search responses now use an
owner-restricted custom view with a five-result selector and shared page
controls. Selecting a result opens its complete indexed source through the
existing lookup formatter without a network request; back restores the exact
search page. Tests cover selection, reference pagination, page restoration,
missing indexed content, ownership, single-message edits, and component limits.

Replaced the result selector with five page-aware numbered buttons after live
interaction review. Their labels correspond to the numbered result cards, so a
full reference opens in one click; empty page slots and all buttons in reference
mode are disabled.
