# Citation plan schema

Read this file when building the JSON plan consumed by `apply_citation_plan.py` and checked by `validate_reference_docx.py`.

## Stable identifiers

For each unique work, use `REF-` plus the first ten uppercase hexadecimal characters of SHA-1 over the normalized Crossref DOI. If DOI is absent, hash the normalized matched title.

## Plan

```json
{
  "replacements": [
    {
      "occurrence_id": "CIT-0001",
      "location_id": "body.p000012",
      "original_text": "Exact full reference text in the manuscript",
      "replacement": "(Smith & Jones, 2025)",
      "ref_ids": ["REF-A1B2C3D4E5"],
      "status": "resolved"
    }
  ],
  "bibliography": {
    "heading": "References",
    "page_break": true,
    "hanging_indent_in": 0.5,
    "line_spacing": 1.0,
    "space_after_pt": 0,
    "entries": [
      {
        "ref_id": "REF-A1B2C3D4E5",
        "text": "Smith, J., & Jones, A. (2025). Example title. Journal Name, 12, 1–9. https://doi.org/10.x/example"
      }
    ]
  }
}
```

Only `resolved` replacements are applied. Keep `ambiguous` and `unresolved` items in the plan so validation can confirm that their original text remains present.

For a single-work citation, one `ref_ids` value automatically links the full replacement. For a multi-work cluster, split the citation so every work has its own link:

```json
{
  "occurrence_id": "CIT-0002",
  "location_id": "body.p000019",
  "original_text": "Two full references to replace",
  "ref_ids": ["REF-A1B2C3D4E5", "REF-F6E7D8C9B0"],
  "replacement_runs": [
    {"text": "("},
    {"text": "Smith, 2025", "ref_id": "REF-A1B2C3D4E5"},
    {"text": "; "},
    {"text": "Jones, 2026", "ref_id": "REF-F6E7D8C9B0"},
    {"text": ")"}
  ],
  "status": "resolved"
}
```

Bibliography `runs` may replace `text` when the style needs mixed formatting such as italic journal titles or volume numbers.
