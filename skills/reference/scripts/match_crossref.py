#!/usr/bin/env python3
"""Match unique supplied titles once against Crossref and emit compact metadata."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_URL = "https://api.crossref.org/works"


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_title(value: Any) -> str:
    text = unicodedata.normalize("NFKC", clean(value)).casefold()
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def first(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if isinstance(value, list) and value:
        return clean(value[0])
    return clean(value)


def year(item: dict[str, Any]) -> str:
    for key in ("issued", "published-print", "published-online", "created"):
        parts = item.get(key, {}).get("date-parts") if isinstance(item.get(key), dict) else None
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            return clean(parts[0][0])
    return ""


def authors(item: dict[str, Any]) -> str:
    rendered: list[str] = []
    for author in item.get("author") or []:
        if not isinstance(author, dict):
            continue
        family = clean(author.get("family"))
        given = clean(author.get("given"))
        name = ", ".join(part for part in (family, given) if part)
        if name:
            rendered.append(name)
    return "; ".join(rendered)


def compact(item: dict[str, Any]) -> dict[str, str]:
    doi = clean(item.get("DOI")).lower()
    return {
        "title": first(item, "title"),
        "authors": authors(item),
        "year": year(item),
        "container_title": first(item, "container-title"),
        "volume": clean(item.get("volume")),
        "issue": clean(item.get("issue")),
        "pages_or_article_number": clean(item.get("page") or item.get("article-number")),
        "publisher": clean(item.get("publisher")),
        "type": clean(item.get("type")),
        "doi": doi,
        "url": f"https://doi.org/{doi}" if doi else clean(item.get("URL")),
    }


def query_crossref(title: str, rows: int, mailto: str) -> dict[str, Any]:
    params = {"query.title": title, "rows": str(rows)}
    if mailto:
        params["mailto"] = mailto
    url = API_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"ReferenceSkill/1.0 (mailto:{mailto})" if mailto else "ReferenceSkill/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"supplied_title": title, "status": "error", "message": clean(exc)}

    items = payload.get("message", {}).get("items", [])
    exact: list[dict[str, Any]] = []
    target = normalize_title(title)
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or normalize_title(first(item, "title")) != target:
            continue
        identity = clean(item.get("DOI")).lower() or normalize_title(first(item, "title"))
        if identity in seen:
            continue
        seen.add(identity)
        exact.append(item)

    if not exact:
        return {"supplied_title": title, "status": "unresolved", "message": "no normalized exact-title Crossref match"}
    if len(exact) > 1:
        return {
            "supplied_title": title,
            "status": "ambiguous",
            "message": "multiple normalized exact-title Crossref matches",
            "candidates": [compact(item) for item in exact],
        }
    return {"supplied_title": title, "status": "matched", "record": compact(exact[0])}


def read_titles(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    values = data.get("titles") if isinstance(data, dict) else data
    if not isinstance(values, list):
        raise ValueError("input must be a JSON array or an object with a titles array")
    unique: dict[str, str] = {}
    for value in values:
        title = clean(value.get("title") if isinstance(value, dict) else value)
        normalized = normalize_title(title)
        if title and normalized not in unique:
            unique[normalized] = title
    return list(unique.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--mailto", default="")
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    try:
        titles = read_titles(args.input_json)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    worker_count = max(1, min(args.workers, 8))
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        results = list(executor.map(lambda value: query_crossref(value, args.rows, args.mailto), titles))

    payload = {
        "source": "Crossref",
        "verification_policy": "one normalized exact-title match; no secondary verification",
        "unique_title_count": len(titles),
        "matched_count": sum(item["status"] == "matched" for item in results),
        "results": results,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Crossref matched {payload['matched_count']} of {len(titles)} unique title(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
