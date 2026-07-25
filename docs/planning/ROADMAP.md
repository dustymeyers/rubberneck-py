# Product Roadmap

Rubberneck is a Discord-based D&D 5e SRD reference and game-master toolkit. It
should make commonly needed information fast to retrieve during play, then grow
into reusable generators for encounters, shops, and loot.

## Feature Block 0: Rule Lookup Foundation

**Status:** Complete

Provide a reliable first vertical slice for looking up 2014 SRD rule sections.

### Acceptance Criteria

- [x] `/rule` retrieves an exact rule section by API index or friendly name.
- [x] Rule names are available through autocomplete.
- [x] Autocomplete does not make an API request per keystroke.
- [x] API access is asynchronous and does not require Redis.
- [x] API responses use a bounded in-memory cache.
- [x] Long rules use one paginated Discord message.
- [x] Pages prefer paragraph and sentence boundaries.
- [x] A section heading is not orphaned from its first paragraph.
- [x] SRD Markdown is normalized for Discord embeds.
- [x] Missing resources and command failures receive user-facing responses.
- [x] Automated tests cover the API client, formatting, pagination, and
  autocomplete metadata.

## Feature Block 1: Unified Rules, Conditions, and Definitions

**Status:** Complete

Turn the current command into a broader reference that includes rule sections,
conditions, and other short SRD definitions without requiring users to know how
the upstream API categorizes a term.

### Proposed Command Surface

- `/rules lookup <term>` searches all supported reference types.

The existing `/rule` command should remain temporarily as a compatibility alias
and direct users toward `/rules lookup`.

### Acceptance Criteria

- [x] `/rules lookup restrained` returns the Restrained condition.
- [x] `/rules lookup cover` returns the Cover rule section.
- [x] Autocomplete combines supported resource types and labels ambiguous
  entries with their type.
- [x] Exact matches rank ahead of prefix and substring matches.
- [x] Results clearly identify their resource type and SRD version.
- [x] Condition descriptions render lists and headings cleanly.
- [x] Adding a new reference endpoint does not require creating another API
  client.
- [x] `/rule` remains functional during the migration and provides a clear
  transition path.
- [x] Tests cover cross-resource lookup, ranking, ambiguity, formatting, and
  the compatibility alias.

## Feature Block 2: Full-Text Rules Search

**Status:** Complete

Allow users to find a rule when they remember a concept or phrase but not the
official title.

### Proposed Command Surface

- `/rules search <text>` searches titles and descriptions.

### Acceptance Criteria

- [x] A query such as `attack while hidden` finds relevant unseen-attacker
  rules even when the phrase is not a title.
- [x] Search covers every resource supported by `/rules lookup`.
- [x] Results rank title matches above description-only matches.
- [x] Results display a short excerpt containing or surrounding the match.
- [x] Matching terms are emphasized without breaking Discord Markdown.
- [x] Results are paginated and capped to a documented maximum.
- [x] Empty, very short, and no-result queries receive useful guidance.
- [x] Search runs locally against cached/indexed SRD content after startup.
- [x] Tests cover ranking, excerpts, highlighting, result limits, and no-result
  behavior.

## Feature Block 3: Related-Rule Navigation

**Status:** Complete

Make it easy to move between concepts commonly referenced together during play.
Search results should also act as a navigable discovery surface rather than a
dead-end summary.

### Proposed Interaction Flow

- A user runs `/rules search <text>`.
- The user chooses one of the displayed results without retyping its title.
- The response opens that result's complete reference text using the standard
  lookup formatting and pagination.
- Back navigation returns to the same search query and result page.

### Acceptance Criteria

- [x] Each search result provides a direct way to open its full reference text.
- [x] Opening a search result reuses lookup formatting and long-text pagination.
- [x] Back navigation restores the originating search query and result page.
- [x] Forward navigation restores the reference and page most recently left by
  back navigation.
- [x] Search-to-reference navigation edits one response instead of creating
  additional channel messages.
- [x] Rule responses can display relevant related rules or conditions.
- [x] A user can navigate to a related entry without typing a new command.
- [x] Navigation edits or paginates one response instead of flooding a channel.
- [x] Back navigation returns to the previous entry and page.
- [x] Related entries are deterministic and explainable, not randomly selected.
- [x] Missing or removed related resources do not break the response.
- [x] The relationship data is stored separately from command presentation.
- [x] Tests cover forward navigation, back navigation, missing relations, and
  interaction ownership.

## Feature Block 4: Reference Quality-of-Life

**Status:** Planned

Round out the reference experience after the core lookup and navigation flows
are stable.

### Candidate Features

- Autocomplete responsiveness improvements based on measured callback and
  end-to-end latency.
- `/rules list [topic]` for browsing by category.
- `/rules compare <first> <second>` for side-by-side concepts.
- `/rules random` for discovery.
- Optional ephemeral/private responses.
- Direct source links where stable URLs are available.
- Server or user preferences for SRD version and response visibility.

### Acceptance Criteria

- [ ] Autocomplete latency is measured separately for local callback execution
  and the end-to-end Discord interaction.
- [ ] Warm autocomplete callbacks meet a documented response-time target for
  representative exact, prefix, substring, and no-result queries.
- [ ] Autocomplete performs no network requests or full-catalog scans per
  keystroke.
- [ ] Index construction time and memory use are measured before choosing
  whether to retain or replace the precomputed substring index.
- [ ] User-facing guidance documents any irreducible Discord client debounce or
  platform delay discovered during testing.
- [ ] Each selected candidate receives its own scoped acceptance criteria before
  implementation begins.
- [ ] Commands share lookup, formatting, caching, and pagination services.
- [ ] User preferences have documented defaults and do not surprise a server.
- [ ] Public responses remain concise enough for active play channels.

## Feature Block 5: Reusable Catalog Foundation and Searchable Bestiary

**Status:** Planned

Build a reusable local catalog framework, then prove it with monsters. The
monster catalog should be useful during play on its own and become the
authoritative monster-data source for random encounter generation. This expands
the modern `/monster` and `/monsters` foundation without coupling bestiary
search to the future generator engine.

### Proposed Command Surface

- `/monster <name>` opens one monster's complete stat reference.
- `/monsters list [filters]` browses the complete catalog.
- `/monsters search [name] [type] [size] [cr] [environment]` finds monsters
  using combinable filters.
- `/monsters random [filters]` selects one monster from the current filter set
  for quick discovery; it does not build a balanced encounter.

The existing `/monster` lookup remains the focused singular command.
`/monsters` evolves into the grouped surface for plural catalog operations.

### Catalog and Data Features

- A generic searchable catalog package shared by monsters, items, spells, and
  character-option resources.
- A small common record base or protocol for identity, display name, source,
  API index, and provenance.
- Resource adapters that normalize endpoint-specific payloads into typed
  records without putting Discord presentation inside data models.
- Shared query, ordering, filtering, autocomplete, seeded selection,
  pagination, and error-result primitives imported by each resource feature.
- Existing standard-library or maintained third-party packages are evaluated
  before custom infrastructure is added; external dependencies stay behind
  project-owned interfaces so they can be tested or replaced.
- A typed in-memory monster record containing identity, challenge rating, XP,
  type, size, alignment, movement, and other generator-relevant fields.
- A locally searchable index loaded once from the SRD API rather than making an
  API request for each search or filter change.
- Project-authored environment and encounter tags stored separately from SRD
  payloads, with explicit provenance.
- A stable query/service interface that both Discord commands and future
  encounter generators can consume.
- Deterministic ordering and optional seeded random selection for repeatable
  tests.

### Acceptance Criteria

- [ ] Users can search monsters by partial name and combine supported filters.
- [ ] Challenge-rating filters support exact values and bounded ranges,
  including fractional ratings.
- [ ] Results show enough context to compare candidates: name, CR, type, size,
  and environment when known.
- [ ] Search results are paginated and can open the selected monster's full
  reference without retyping its name.
- [ ] Search and autocomplete run locally after startup with no API request per
  interaction.
- [ ] The reusable catalog framework is generic over typed records and does not
  contain monster-specific branches.
- [ ] Shared behavior uses composition, protocols, or shallow inheritance;
  resource-specific adapters own only parsing, filters, and display metadata.
- [ ] Catalog, filtering, and paginator implementations live in reusable
  packages and are imported rather than copied into each cog.
- [ ] New dependencies document the duplicated code they replace, their
  maintenance health, and why the standard library or current packages are
  insufficient.
- [ ] Monster payloads are normalized into typed records before indexing.
- [ ] Environment or encounter tags are editable independently of command code
  and are clearly distinguished from SRD-sourced fields.
- [ ] Monsters without project-authored environment tags remain discoverable
  unless an environment filter is explicitly applied.
- [ ] The catalog exposes a reusable filtered result set for Block 7 encounter
  generation rather than embedding generator rules in Discord commands.
- [ ] Random selection can be seeded for deterministic tests and does not claim
  to produce a balanced encounter.
- [ ] Empty catalogs, invalid filter combinations, API failures, and no-result
  searches receive useful user-facing responses.
- [ ] Tests cover normalization, fractional CR values, combined filters,
  ordering, pagination, detail navigation, provenance, and seeded selection.

## Feature Block 6: Items and Character Compendium

**Status:** Planned

Expand the Block 5 catalog framework across the other SRD resources players and
game masters routinely browse. Equipment becomes the authoritative item source
for shops and loot, while spells and character options form a unified
character-reference compendium.

### Proposed Command Surface

- `/item <name>` and `/items search [name] [category] [cost] [rarity]`
- `/spell <name>` and `/spells search [class] [level] [school] [ritual]`
- `/class <name>` and `/classes list`
- `/subclass <name>` and `/subclasses list [class]`
- `/background <name>` and `/backgrounds list`
- `/species lookup <name>` and `/species list` for species/races
- `/feat <name>` and `/feats search [name] [prerequisite]`

Singular commands provide direct lookup. Plural commands provide browsing,
search, comparison, and filtering. User-facing copy should say "species" while
retaining compatibility with upstream API fields or searches that use "race."

### Resource Features

- Items and equipment: weapons, armor, adventuring gear, tools, mounts,
  vehicles, magic items, category, cost, weight, mechanical properties, rarity
  when available, and project-authored shop/settlement tags.
- Spells: level, school, casting time, range, duration, concentration, ritual,
  components, damage/healing metadata, and class availability.
- Classes and subclasses: hit die, proficiencies, saving throws, levels,
  features, spellcasting, and parent-class relationships.
- Backgrounds: proficiencies, languages, equipment, features, and suggested
  characteristics.
- Species/races and subraces: size, speed, traits, languages, bonuses, and
  parent-child relationships.
- Feats: prerequisites, benefits, and relationships to referenced rules or
  character options.

### Acceptance Criteria

- [ ] Every resource family uses the Block 5 generic catalog and API client
  rather than introducing a parallel cache or search implementation.
- [ ] Each endpoint has a typed record and adapter with explicit handling for
  missing or version-dependent fields.
- [ ] Lookup, autocomplete, filter semantics, result navigation, provenance,
  and error handling are consistent across resource families.
- [ ] Items support reusable filters and tags needed by Block 7 shop and loot
  generators without embedding shop-generation logic in item commands.
- [ ] Spell searches support combinable class, level, school, ritual, and
  concentration filters.
- [ ] Classes, subclasses, species/subraces, and related features preserve
  their parent-child relationships for navigation.
- [ ] "Species" and legacy "race" terminology resolve to the same underlying
  SRD resources without duplicating records.
- [ ] Resource-specific formatters compose shared embed and pagination helpers
  while retaining fields appropriate to that resource.
- [ ] Adding another SRD endpoint requires an adapter, typed record, filter
  specification, and formatter—not another API client or copied cog framework.
- [ ] Tests share reusable contract suites for every catalog adapter and add
  focused coverage for resource-specific normalization and filters.

## Feature Block 7: Game-Master Generators

**Status:** Planned — later phase

Build a reusable weighted-table engine before implementing separate generators.

### Candidate Features

- Random encounters using the Block 5 monster catalog, filtered by environment
  and party parameters.
- Shop inventories using the Block 6 item catalog, filtered by settlement and
  shop type.
- Loot tables using the Block 6 item catalog, filtered by tier, source, and
  theme.

### Acceptance Criteria

- [ ] Table data is editable independently of command code.
- [ ] The generator supports weighted entries and nested tables.
- [ ] Seeded generation produces deterministic results for tests.
- [ ] Invalid table data fails validation with actionable messages.
- [ ] Encounter, shop, and loot commands share the same generation engine.
- [ ] Encounter generation consumes the searchable bestiary service rather
  than maintaining a second monster list or fetching monsters per request.
- [ ] Shop and loot generation consume the shared item catalog rather than
  maintaining separate equipment arrays.
- [ ] SRD/API-derived content is distinguishable from project-authored tables.
