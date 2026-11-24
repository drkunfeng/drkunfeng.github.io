#!/usr/bin/env python3
"""Rebuild the publication list in publications.html from a Scopus RIS export.

Usage (from the repository root):
    python3 tools/build_publications.py data/scopus.ris

Export from Scopus: Author profile > Documents > select all > Export > RIS.
Everything between the PUBLICATIONS:START and PUBLICATIONS:END markers in
index.html is replaced.
"""
import html
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "publications.html"
ME = "Feng, K."

# Tidy Scopus venue names for display.
VENUE_FIX = {
    "SDHM Structural Durability and Health Monitoring": "Structural Durability and Health Monitoring",
    "Applied Sciences (Switzerland)": "Applied Sciences",
}
AUTHOR_FIX = {"Obrien, E.J.": "O’Brien, E. J.", "OBrien, E.J.": "O’Brien, E. J.",
              "Obrien, E.": "O’Brien, E.", "O'Higgins, C.": "O’Higgins, C."}


def parse_ris(text):
    recs, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY":
            cur = defaultdict(list)
            cur["TY"] = [val]
        elif tag == "ER":
            if cur is not None:
                recs.append(cur)
            cur = None
        elif cur is not None:
            cur[tag].append(val)
    return recs


def fmt_author(a):
    a = AUTHOR_FIX.get(a, a)
    # "Taylor, S." stays; "Fayyad, T.M." -> "Fayyad, T. M."
    a = re.sub(r"\.(?=[A-Z])", ". ", a)
    e = html.escape(a)
    return f"<strong>{e}</strong>" if a.startswith("Feng, K") else e


def first(r, tag, default=""):
    return r[tag][0] if r.get(tag) else default


def entry(r):
    title = html.escape(first(r, "TI"))
    doi = first(r, "DO")
    authors = ", ".join(fmt_author(a) for a in r["AU"])
    venue = first(r, "T2")
    venue = html.escape(VENUE_FIX.get(venue, venue))
    vol, iss = first(r, "VL"), first(r, "IS")
    art, sp, ep = first(r, "C7"), first(r, "SP"), first(r, "EP")
    bits = []
    if vol:
        bits.append(html.escape(vol) + (f"({html.escape(iss)})" if iss else ""))
    if art:
        bits.append(html.escape(art))
    elif sp:
        bits.append(f"{sp}–{ep}" if ep else sp)
    detail = (", " + ", ".join(bits)) if bits else ""
    head = (f'<a href="https://doi.org/{html.escape(doi)}" target="_blank" rel="noopener noreferrer">{title}</a>'
            if doi else title)
    return (f'            <h3>{head}</h3>\n'
            f'            <p class="pub-meta">{authors}{"" if authors.endswith(".") or authors.endswith(".</strong>") else "."} <em>{venue}</em>{detail}.</p>\n')


def block(recs, heading, gid):
    recs = sorted(recs, key=lambda r: (-int(first(r, "PY", "0")), first(r, "TI").lower()))
    out = [f'      <h3 class="pub-group" id="{gid}">{heading} <span class="count">{len(recs)}</span></h3>\n',
           '      <ol class="pubs">\n']
    last = None
    for r in recs:
        y = first(r, "PY")
        if y == last:
            yr = f'<div class="pub-year repeat" aria-hidden="true">{y}</div>'
        else:
            yr = f'<div class="pub-year">{y}</div>'
        last = y
        out.append(f'        <li class="pub">\n          {yr}\n          <div>\n{entry(r)}          </div>\n        </li>\n')
    out.append('      </ol>\n')
    return "".join(out)


def main(ris_path):
    recs = parse_ris(Path(ris_path).read_text(encoding="utf-8-sig"))
    journals = [r for r in recs if first(r, "TY") == "JOUR"]
    confs = [r for r in recs if first(r, "TY") != "JOUR"]
    export = ""
    for r in recs:
        for n in r.get("N1", []):
            if n.startswith("Export Date:"):
                export = n.split(":", 1)[1].strip()
    month_year = " ".join(export.split()[1:]) if export else ""
    note = f"All {len(recs)} publications indexed in Scopus" + (f", updated {month_year}." if month_year else ".")

    section = (
        '  <section class="section" id="publications">\n'
        '    <nav class="pub-side" aria-label="Publication types">\n'
        f'      <a href="#journal-articles">Journal articles <span>{len(journals)}</span></a>\n'
        f'      <a href="#conference-papers">Conference papers <span>{len(confs)}</span></a>\n'
        '    </nav>\n'
        '    <div class="body">\n'
        f'      <p class="pub-note">{note} My name is in bold. Citation counts are on <a href="https://scholar.google.com/citations?user=854eu74AAAAJ&amp;hl=en" target="_blank" rel="noopener noreferrer">Google Scholar</a>.</p>\n'
        + block(journals, "Journal articles", "journal-articles")
        + block(confs, "Conference papers", "conference-papers")
        + '    </div>\n  </section>\n'
    )
    s = INDEX.read_text(encoding="utf-8")
    s = re.sub(r"(<!-- PUBLICATIONS:START -->\n).*?(\s*<!-- PUBLICATIONS:END -->)",
               lambda m: m.group(1) + section + m.group(2).lstrip("\n").rjust(0), s, flags=re.S)
    INDEX.write_text(s, encoding="utf-8")
    print(f"{len(journals)} journal articles, {len(confs)} conference papers")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data" / "scopus.ris")
