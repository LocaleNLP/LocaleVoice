# LocaleVoice — Knowledge Quality Audit (Milestone 4E, Phase 3)

Date: 2026-11-04. Auditor: engineering (automated page comparison + manual review).
Corpus version: `m4d-1.0.0` (`data/knowledge/documents.jsonl`, 4 documents).

## Method

Each `source_url` was fetched live (HTTP 200, 135–330 KB) and stripped to
text. Every excerpt sentence was checked for verbatim presence on its page
(whitespace- and citation-spacing-normalized), in order. Every keyword was
checked for verbatim presence on its page. Publisher names and the
`source_updated_at` stamps were checked against page content.

## Per-document status

| Doc | Source retrieved | Excerpt extracted | Provenance verified | Content reviewed |
|---|---|---|---|---|
| feedipedia-cowpea-seeds | yes (node/232, 200) | yes, verbatim contiguous | yes | yes (4D) |
| feedipedia-olive-cake | yes (node/32, 200) | yes, verbatim, one elision | yes | yes (4D) |
| feedipedia-wheat-grain | yes (node/223, 200) | yes, verbatim, two elisions | yes | yes (4D) |
| feedipedia-alfalfa | yes (node/275, 200) | yes, verbatim, one elision | yes | **PENDING** |

Definitions:

- *Source retrieved*: the URL returns the expected Feedipedia datasheet.
- *Excerpt extracted*: the stored text comes from that page.
- *Provenance verified*: every excerpt sentence appears verbatim on the
  page, in order; all keywords appear verbatim on the page; publisher
  names (INRAE, CIRAD, AFZ, FAO) and the `source_updated_at` stamp match
  the page (`Last updated on` stamps: 26/11/2015, 24/10/2012,
  21/02/2013, 28/11/2012 respectively).
- *Content reviewed*: a second person confirmed the excerpt is a fair,
  in-context representation. Alfalfa has provenance only.

## Elision notes (no sentence rewritten)

- cowpea: all 5 sentences contiguous on the page (citation-link spacing
  only: `(Gomez, 2004)` vs rendered `( Gomez, 2004 )`).
- olive-cake: sentences 1–2 contiguous; a ~5 KB section (general
  description tables) is elided before the palatability passage, whose
  sentences are contiguous after it.
- wheat-grain: two small elisions (423 and 287 chars of intervening
  trial-detail clauses) between three contiguous passages.
- alfalfa: one 210-char elision between two contiguous passages.

All excerpts preserve sentence order and wording; elisions only remove
middle material. No excerpt sentence was paraphrased or reordered.

## Field audit

- `id`, `title`: match the datasheet subject on all four pages.
- `source_name`: all four publisher names present on all four pages.
- `category`: Legumes / Feed by-products / Cereals / Forage — correct.
- `crop_or_species`: accurate feed-use summaries.
- `keywords`: 14/14 observed verbatim on their pages (common-names
  lists). Used for lexical matching only, per manifest policy.
- `review_status`: `verified-excerpt` × 3, `pending-review` (alfalfa).
  Alfalfa MUST stay `pending-review` until the second-person content
  review above is done; provenance alone does not clear it.

## Correction made in this phase

- `data/knowledge/manifest.json`: the excerpt policy claimed all records
  were "retrieved on the created_at date"; alfalfa was curated later
  (`date_accessed` 2026-11-04). The policy now points at each record's
  `date_accessed`. Corpus re-validated (`validate_corpus.py`, exit 0).

## Coverage statement (unchanged)

Four short excerpts on livestock feeding. No new material was collected;
no coverage claim is increased. Most questions will correctly abstain.
