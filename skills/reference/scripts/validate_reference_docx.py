#!/usr/bin/env python3
"""Validate citations, bibliography entries, bookmarks, and internal links in a DOCX."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

from docx import Document
from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def rendered(value: dict, runs_key: str, text_key: str) -> str:
    runs = value.get(runs_key)
    if isinstance(runs, list) and runs:
        return "".join(str(run.get("text", "")) for run in runs)
    return str(value.get(text_key, ""))


def bookmark_name(ref_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", ref_id.strip())
    if not cleaned or not cleaned[0].isalpha():
        cleaned = "REF_" + cleaned
    return cleaned[:40]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revised_docx", type=Path)
    parser.add_argument("plan_json", type=Path)
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()

    try:
        Document(args.revised_docx)
        plan = json.loads(args.plan_json.read_text(encoding="utf-8-sig"))
        with zipfile.ZipFile(args.revised_docx) as archive:
            root = etree.fromstring(archive.read("word/document.xml"))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # Read visible text from the package XML so citations inside tables and
    # hyperlink elements are included in validation.
    text = "\n".join(
        "".join(paragraph.xpath(".//w:t/text()", namespaces={"w": W_NS}))
        for paragraph in root.xpath("//w:p", namespaces={"w": W_NS})
    )
    bookmarks = set(root.xpath("//w:bookmarkStart/@w:name", namespaces={"w": W_NS}))
    anchors = Counter(root.xpath("//w:hyperlink/@w:anchor", namespaces={"w": W_NS}))
    errors: list[str] = []

    entries = plan.get("bibliography", {}).get("entries") or []
    bibliography_ids: set[str] = set()
    for entry in entries:
        entry_text = rendered(entry, "runs", "text")
        ref_id = str(entry.get("ref_id") or "").strip()
        if entry_text and entry_text not in text:
            errors.append(f"bibliography entry missing: {entry_text[:100]}")
        if not ref_id:
            errors.append(f"bibliography entry lacks Ref_ID: {entry_text[:100]}")
            continue
        bibliography_ids.add(ref_id)
        if bookmark_name(ref_id) not in bookmarks:
            errors.append(f"bibliography bookmark missing: {ref_id}")

    expected_links: Counter[str] = Counter()
    resolved_count = 0
    for item in plan.get("replacements") or []:
        original = str(item.get("original_text") or "")
        if item.get("status") != "resolved":
            if original and original not in text:
                errors.append(f"unresolved original text was removed: {original[:100]}")
            continue
        resolved_count += 1
        citation = rendered(item, "replacement_runs", "replacement")
        if citation and citation not in text:
            errors.append(f"citation missing: {citation}")
        ref_ids = {str(value) for value in item.get("ref_ids") or [] if str(value).strip()}
        runs = item.get("replacement_runs")
        linked_ids = {
            str(run.get("ref_id"))
            for run in runs
            if str(run.get("ref_id") or "").strip()
        } if isinstance(runs, list) and runs else (set(ref_ids) if len(ref_ids) == 1 else set())
        for ref_id in sorted(ref_ids - linked_ids):
            errors.append(f"citation lacks link segment for {ref_id}: {item.get('occurrence_id', '')}")
        for ref_id in linked_ids:
            if ref_id not in bibliography_ids:
                errors.append(f"citation links to absent bibliography entry: {ref_id}")
            expected_links[bookmark_name(ref_id)] += 1

    for target, count in expected_links.items():
        if anchors[target] < count:
            errors.append(f"links to {target}={anchors[target]}, expected at least {count}")

    report = {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "resolved_occurrences": resolved_count,
        "bibliography_entries": len(entries),
        "internal_hyperlinks": sum(anchors.values()),
    }
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 3 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
