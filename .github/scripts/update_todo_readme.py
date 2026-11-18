#!/usr/bin/env python3
"""Sync the README Complete TODO List with the current dev branch TODO comments.

The existing README list is treated as the baseline. Entries for the two Python
files changed on dev are regenerated from the current source; all other entries
are preserved exactly and the complete list is re-sorted in the documented order.
"""
from pathlib import Path
import re

TITLE = "### \U0001f4dd Complete TODO List"
CHANGED_FILES = (
    "luffy/deepscaler/utils.py",
    "luffy/verl/verl/protocol.py",
)
ENTRY_RE = re.compile(
    r"^- \[ \] \*\*(?P<path>.+?):(?P<line>\d+)\*\* - (?P<msg>.*)$"
)
TODO_RE = re.compile(r"#.*\bTODO\b")


def parse_entries(section_text):
    entries = []
    for raw in section_text.splitlines():
        match = ENTRY_RE.match(raw.strip())
        if match:
            entries.append(
                (
                    match.group("path"),
                    int(match.group("line")),
                    match.group("msg"),
                )
            )
    return entries


def extract_todos(path, text):
    rows = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if not TODO_RE.search(raw):
            continue
        after = raw.split("TODO", 1)[1]
        message = after.lstrip(": ").strip()
        if message:
            rows.append((path, lineno, message))
    return rows


def rebuild_readme(text, changed_contents):
    title_pos = text.index(TITLE)
    title_line_end = text.index("\n", title_pos)
    next_heading = text.find("\n## ", title_line_end + 1)
    if next_heading == -1:
        heading_start = len(text)
        heading_suffix = ""
    else:
        heading_start = next_heading + 1
        heading_suffix = text[heading_start:]

    prefix = text[: title_line_end + 1]
    old_section = text[title_line_end + 1 : heading_start]
    old_entries = parse_entries(old_section)

    unchanged_entries = [entry for entry in old_entries if entry[0] not in changed_contents]
    rows = list(unchanged_entries)

    for path, content in changed_contents.items():
        rows.extend(extract_todos(path, content))

    rows.sort(key=lambda entry: (entry[0], entry[1]))
    item_lines = [
        f"- [ ] **{path}:{line}** - {message}"
        for path, line, message in rows
    ]
    body = "\n" + "\n".join(item_lines) + "\n\n"
    return prefix + body + heading_suffix, rows, old_entries


def main():
    root = Path.cwd()
    readme_path = root / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    if TITLE not in text:
        raise SystemExit("Complete TODO List heading was not found in README.md")

    changed_contents = {}
    for rel_path in CHANGED_FILES:
        source_path = root / rel_path
        if not source_path.is_file():
            raise FileNotFoundError(f"Changed source file not found: {rel_path}")
        changed_contents[rel_path] = source_path.read_text(encoding="utf-8")

    updated_text, rows, old_entries = rebuild_readme(text, changed_contents)
    readme_path.write_text(updated_text, encoding="utf-8")

    print(f"Baseline entries parsed: {len(old_entries)}")
    print(f"Updated TODO entries: {len(rows)}")
    for path in CHANGED_FILES:
        current = extract_todos(path, changed_contents[path])
        print(f"  {path}: {len(current)} current TODO entries")
        for _, line, message in current:
            print(f"    L{line}: {message}")


if __name__ == "__main__":
    main()
