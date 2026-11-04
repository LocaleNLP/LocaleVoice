# Knowledge Corpus — Curation Process (Milestone 4D)

`documents.jsonl` holds short verified excerpts, one JSON object per
line, plus this manifest. Current coverage: 3 Feedipedia excerpts
(cowpea, olive cake, wheat grain). Never claim broader coverage than
the manifest lists.

## Schema (required fields)

`id`, `title`, `source_name`, `source_url`, `category`,
`crop_or_species`, `excerpt`, `keywords`, `language`, `date_accessed`,
`review_status`. Optional extras (preserved verbatim):
`usage_or_license_notes`, `source_updated_at`.

`category` must be one of: Cereals, Legumes, Animal nutrition, Feed
ingredients, Feed by-products, Forage, Livestock.

## Adding a genuine excerpt

1. Pick a source page from an authoritative publisher (prefer official
   Moroccan agricultural authorities, public research institutes, or
   reputable international agricultural organizations).
2. Check the site's access rules first (`/robots.txt`, terms of use).
   If automated fetching is disallowed or blocked, transcribe by hand
   from a browser you may use — never bypass access controls.
3. Fetch or read the page. Copy a short passage **verbatim** (only
   whitespace normalization is allowed). Record the page's own
   last-updated date as `source_updated_at` when shown.
4. `keywords`: terms observed verbatim on the same page (common-names
   list, excerpt, references) that help French/Arabic-script matching.
   Never invent keywords.
5. `date_accessed`: the day you retrieved it. `review_status` starts
   at `verified-excerpt` only after a second person confirms the text
   matches the source; otherwise use `pending-review`.
6. Run `python scripts/validate_corpus.py` — it must pass.
7. Re-run `python -m pytest -q` and `python scripts/evaluate_pipeline.py`.

## Forbidden

- Inventing agricultural facts, quotations, URLs, or dates.
- Reconstructing "likely" content from a page title or snippet.
- Storing full articles (short excerpts only, with attribution).
- Redistributing beyond this prototype without checking source terms.
