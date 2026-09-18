---
name: reference
description: Quickly convert sentence-adjacent full references in a Word manuscript into journal-formatted in-text citations and a final bibliography, with clickable Word links between each citation and its bibliography entry. Use when the user supplies a DOCX manuscript plus citation and reference-format requirements and wants a finished cited DOCX. Match metadata once in Crossref only; consult ISSN LTWA only when the requested style requires abbreviated journal titles. Do not discover new literature or perform secondary verification.
---

# Reference

Create one finished cited Word document with minimal research, tool calls, and chat output.

## Required input

Require:

1. a `.docx` manuscript containing each full reference after the sentence it supports; and
2. the required in-text citation and bibliography format, preferably copied from the journal.

Preserve the source file and write a new DOCX. Do not add literature unless explicitly requested.

## Fast workflow

1. Run `scripts/docx_inventory.py` and work from its candidate paragraphs rather than loading the whole manuscript into conversation.
2. Extract the supplied work title from each full-reference block. Treat the title as the search anchor; other supplied fields are clues only.
3. Normalize titles, deduplicate them, and run `scripts/match_crossref.py` once for the unique-title list.
4. Accept one normalized exact-title Crossref match as final. Do not open publisher pages, DOI pages, Google Scholar, journal sites, or a second metadata database. If Crossref returns no unique exact match, keep the original block and mark it unresolved instead of guessing.
5. Parse the requested style once. Query ISSN LTWA only when the style explicitly requires abbreviated journal titles; otherwise keep the Crossref container title unchanged.
6. Read [references/plan-schema.md](references/plan-schema.md), build one citation plan, then run `scripts/apply_citation_plan.py`.
7. Run `scripts/validate_reference_docx.py`. Resolve structural failures before delivery; leave metadata exceptions visibly unresolved.

Batch independent Crossref work, reuse each matched record for all occurrences, and avoid narrating intermediate results.

## Formatting and links

- Apply the user's rules for author names, year suffixes, `et al.`, citation clusters, bibliography order, title case, italics, punctuation, DOI display, hanging indents, spacing, and journal abbreviation.
- Give every resolved work a stable `Ref_ID`.
- Create a Word bookmark on every bibliography entry and an internal hyperlink from every in-text citation to the matching bookmark.
- For a multi-work citation, link each author-year or number segment to its own bibliography entry.
- Keep hyperlinks visually identical to surrounding citation text; do not force blue or underlined styling.
- Treat links as navigation links, not EndNote fields. Regenerate the document if metadata or style requirements change.

## Safety

- Replace only exact source text at the recorded Word location.
- Never delete prose merely because it resembles a reference.
- Keep ambiguous or unmatched reference blocks unchanged.
- Preserve unrelated text, tables, figures, equations, section order, and formatting.
- Deduplicate by Crossref DOI, then normalized Crossref title. Preserve genuinely distinct versions.

## Output

Return only:

- `<manuscript>_referenced.docx`; and
- a short count of unique works, replaced occurrences, and unresolved blocks.

Do not paste the bibliography, Crossref metadata, or processing log into chat. Create an Excel or metadata file only when the user explicitly requests one.
