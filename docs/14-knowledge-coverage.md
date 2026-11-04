# Knowledge Coverage and Review Status (Milestone 5)

Corpus `m4d-1.0.0`, 4 Feedipedia excerpts. Provenance audit:
`docs/10-knowledge-audit-4e.md`. No new excerpts were added in this
milestone.

## Covered topics (answerable)

| Doc | Answers questions about |
|---|---|
| feedipedia-cowpea-seeds (`verified-excerpt`) | What cowpea is; food vs feed use; hay/silage as fodder |
| feedipedia-olive-cake (`verified-excerpt`) | Olive by-products as feed; palatability and molasses blending; roughage comparison; feeding forms; 40% lamb inclusion |
| feedipedia-wheat-grain (`verified-excerpt`) | Wheat as ruminant energy source; replacing maize; palatability; fermentation risks (bloat, laminitis, acidosis) |
| feedipedia-alfalfa (`pending-review`) | Alfalfa suitability for ruminants; grazing/hay/silage forms; palatability differences |

Alfalfa stays `pending-review` until a second person confirms the
excerpt is a fair, in-context representation (provenance alone does
not clear it). It remains retrievable — retrieval does not filter on
review status — so validation answers citing it must be checked
against the source page listed in `source_url`.

## Explicitly unsupported (must abstain or clarify)

- Crop choice by region, soil analysis interpretation, rainfall and
  seasonal advice, irrigation schedules → clarification flow, then
  abstention (`docs/09`, scenarios 3–5).
- Treatment, dosage, pesticide, and veterinary instructions →
  generic abstention; never guessed.
- Anything outside agriculture (capitals, sport, etc.) →
  unsupported-domain message, no model call.
- All crops, animals, and feeds beyond the four excerpts above →
  abstention. This is most of real farming: the narrow coverage is
  by design at this stage.

## Adding material (unchanged bar)

Manual curation per `data/knowledge/README.md`: excerpt copied
verbatim from the public source page, keywords observed verbatim on
that page, `source_updated_at` checked against the page stamp,
`review_status: pending-review` until a second person clears it. No
excerpt from titles alone; no coverage claim without collected text.
