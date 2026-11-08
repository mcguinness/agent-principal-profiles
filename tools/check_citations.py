#!/usr/bin/env python3
"""Check that every cited section of another specification is one a person verified.

Each draft cites sections as {{Section N of REF}} or {{Appendix N of REF}}.
tools/cited-sections.json records, for each cited document at the exact
revision the drafts reference (I-D.name-NN, or RFCnnnn), the heading of
every section the drafts cite, as a person verified it.

Default (offline, run in CI): fails when an Internet-Draft reference is not
pinned to a revision, or when a draft cites a section of a document and
revision that the manifest does not record. Re-pinning a dependency
therefore fails until the cited sections are verified again at the new
revision.

--fetch: also downloads each cited revision (ietf.org archive, rfc-editor.org)
into a cache and fails when a recorded heading differs from the heading at
that section number, or the section does not exist. Run it whenever the
manifest changes.

--fetch --update: records the fetched heading for every citation the
manifest lacks, removes entries no draft cites, and prints each new entry
with its citing sentence for review. Review that output before committing:
it is the verification.

The check detects renumbering, missing sections and unverified citations.
It does not detect a citation that names a real section whose text does
not support the sentence citing it; only reading the section does that.

References the drafts define inline (with a title, such as the family's own
drafts) are not checked.
"""
import argparse
import glob
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "tools", "cited-sections.json")
CACHE = os.environ.get("CITATION_CACHE",
                       os.path.join(os.path.expanduser("~"), ".cache", "governed-agent-citations"))

REFERENCE = re.compile(r"^  ([A-Za-z0-9._-]+):[ \t]*(\S[^\n]*)?$", re.M)
# Whitespace inside a citation may include a line break.
CITATION = re.compile(r"\{\{(Section|Appendix)\s+([0-9A-Z][0-9A-Za-z.]*)\s+of\s+"
                      r"([A-Za-z0-9._-]+)\}\}")
# A section heading at column 0: "4.1.  Title", "A.1.  Title" or "Appendix A.  Title".
HEADING = re.compile(r"^(?:Appendix )?((?:\d+|[A-Z])(?:\.\d+)*)\.?[ \t]+(\S.*)$")


def references(text):
    """The draft's references: anchor -> document (I-D.name-NN, I-D.name, or RFCnnnn)."""
    refs = {}
    head = text.split("\n--- abstract", 1)[0]
    for anchor, value in REFERENCE.findall(head):
        value = (value or "").strip()
        if value.startswith("I-D."):
            refs[anchor] = value
        elif not value and re.fullmatch(r"RFC\d+", anchor):
            refs[anchor] = anchor
    return refs


def citations():
    """Yield (draft, line, anchor, section, document, sentence) for every external citation."""
    for path in sorted(glob.glob(os.path.join(ROOT, "draft-*.md"))):
        text = open(path, encoding="utf-8").read()
        refs = references(text)
        for match in CITATION.finditer(text):
            section, anchor = match.group(2).rstrip("."), match.group(3)
            if anchor not in refs:
                continue   # a family draft or another inline reference
            line = text.count("\n", 0, match.start()) + 1
            start = max(text.rfind("\n\n", 0, match.start()), 0)
            end = text.find("\n\n", match.end())
            sentence = " ".join(text[start:end if end > 0 else None].split())
            yield os.path.basename(path), line, anchor, section, refs[anchor], sentence


def unpinned():
    """Internet-Draft references with no revision number."""
    found = []
    for path in sorted(glob.glob(os.path.join(ROOT, "draft-*.md"))):
        for anchor, document in references(open(path, encoding="utf-8").read()).items():
            if document.startswith("I-D.") and not re.search(r"-\d{2}$", document):
                found.append((os.path.basename(path), anchor, document))
    return found


def source_url(document):
    if document.startswith("RFC"):
        return f"https://www.rfc-editor.org/rfc/rfc{document[3:]}.txt"
    return f"https://www.ietf.org/archive/id/draft-{document[4:]}.txt"


def fetch(document):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, document + ".txt")
    if not os.path.exists(path):
        req = urllib.request.Request(source_url(document),
                                     headers={"User-Agent": "governed-agent-citations"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(path, "wb") as out:
            out.write(data)
    return open(path, encoding="utf-8", errors="replace").read()


def headings(text):
    """Section number -> the first line of its heading, from rendered text."""
    found = {}
    for line in text.splitlines():
        if not line or line[0] == " ":
            continue
        # Table-of-contents lines are indented, so only headings, page
        # headers and footers start at column 0.
        match = HEADING.match(line.rstrip())
        if match:
            found.setdefault(match.group(1), match.group(2).strip())
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                     epilog="Re-pinning: change the pin, then run with "
                                            "--fetch --update and review what it prints.")
    parser.add_argument("--fetch", action="store_true",
                        help="compare recorded headings with each pinned revision's text")
    parser.add_argument("--update", action="store_true",
                        help="with --fetch: record missing entries and drop unused ones")
    args = parser.parse_args()
    if args.update and not args.fetch:
        parser.error("--update needs --fetch")

    manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    failures = []
    for draft, anchor, document in unpinned():
        failures.append(f"{draft}: {anchor} references {document} with no revision")

    cited = {}
    for draft, line, anchor, section, document, sentence in citations():
        cited.setdefault((document, section), []).append((draft, line, anchor, sentence))

    fetched = {}
    if args.fetch:
        for document in sorted({d for d, _ in cited}):
            try:
                fetched[document] = headings(fetch(document))
            except OSError as err:
                failures.append(f"{document}: cannot fetch {source_url(document)}: {err}")

    added = []
    for (document, section), uses in sorted(cited.items()):
        recorded = manifest.get(document, {}).get(section)
        actual = fetched.get(document, {}).get(section) if document in fetched else None
        where = ", ".join(f"{d}:{n} ({a})" for d, n, a, _ in uses)
        if args.fetch and document in fetched and actual is None:
            failures.append(f"{document} has no Section {section}, cited at {where}")
            continue
        if recorded is None:
            if args.update and actual is not None:
                manifest.setdefault(document, {})[section] = actual
                added.append((document, section, actual, uses))
            else:
                failures.append(f"{document} Section {section} is not verified "
                                f"(cited at {where})")
        elif actual is not None and actual != recorded:
            failures.append(f"{document} Section {section} is now \"{actual}\", "
                            f"verified as \"{recorded}\" (cited at {where})")

    unused = [(d, s) for d, secs in manifest.items() for s in secs if (d, s) not in cited]
    if args.update:
        for document, section in unused:
            del manifest[document][section]
        manifest = {d: dict(sorted(s.items(), key=lambda kv: [
                        (0, int(p)) if p.isdigit() else (1, p) for p in kv[0].split(".")]))
                    for d, s in sorted(manifest.items()) if s}
        with open(MANIFEST, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2, sort_keys=False)
            out.write("\n")
        for document, section, heading, uses in added:
            print(f"+ {document} Section {section}: {heading}")
            for draft, line, anchor, sentence in uses:
                print(f"    {draft}:{line}: {sentence[:300]}")
        for document, section in unused:
            print(f"- {document} Section {section}: no longer cited")
    else:
        for document, section in unused:
            print(f"note: {document} Section {section} is recorded but no draft cites it")

    for failure in failures:
        print(f"FAIL {failure}")
    total = sum(len(u) for u in cited.values())
    print(f"{len(cited)} cited sections ({total} citations) in "
          f"{len({d for d, _ in cited})} documents; {len(failures)} failures"
          + (f"; {len(added)} recorded" if args.update else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
