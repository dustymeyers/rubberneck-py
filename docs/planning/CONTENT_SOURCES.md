# Content Sources and Provenance

Rubberneck must audit code and game content separately. A repository's software
license does not automatically license the rules text, images, or other data
stored in or consumed by that software.

This is a project policy, not legal advice.

## Approved Default Boundary

### D&D 5e SRD 5.1 (2014 rules)

- **Status:** Approved for import and display.
- **Content license:** Creative Commons Attribution 4.0 International
  (CC BY 4.0).
- **Canonical source:** Wizards of the Coast's SRD 5.1 document.
- **Required action:** Preserve the attribution statement supplied by Wizards
  anywhere Rubberneck distributes or displays SRD-derived content.
- **Provider:** dnd5eapi.co may supply normalized SRD records, but Rubberneck
  should retain the SRD version and upstream provider as separate provenance
  fields.

The existing monster, rule, and condition features remain inside this boundary.
Future SRD items, spells, classes, subclasses, backgrounds, species, and feats
may use the same policy after verifying each record belongs to SRD 5.1.

## Evaluated Providers

### 5e-bits / dnd5eapi.co

- The API and database repositories use MIT-licensed software.
- The database repository identifies its underlying game material as OGL 1.0a
  content.
- Rubberneck may continue consuming its 2014 SRD endpoints, but must attribute
  the game content under the selected SRD license rather than treating the
  database's MIT software license as a content license.
- Before importing a new endpoint, verify that every included record belongs to
  the selected SRD version and record the endpoint, upstream revision, and
  content license.

### 5e.tools

- The application source is MIT licensed.
- That MIT license establishes permission for the application code, not blanket
  permission to redistribute the catalog data sourced from many books.
- The public repository's presence and a user's ownership of sourcebooks do not
  grant Rubberneck redistribution rights.
- **Status:** Suitable for studying reusable software and provider ideas. Do not
  import or redistribute non-SRD catalog data without a separate license or
  explicit permission for each source.
- Human-facing links may be evaluated separately from copying content, but links
  must be stable, useful, and appropriate for the intended deployment.

## Import Gate

Every new provider or catalog expansion must record:

1. Provider and exact upstream revision or API version.
2. Original publication/source for each content family.
3. Content license or explicit permission, separate from the software license.
4. Required attribution and notices.
5. Whether text, structured facts, images, and trademarks have different terms.
6. A validation rule that prevents records outside the approved source set from
   entering the production catalog.

If any field is unknown, the content is not imported. Provider adapters should
expose provenance metadata so presentation layers can display the correct
source and attribution without hard-coding provider-specific text.
