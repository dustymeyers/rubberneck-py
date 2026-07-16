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
