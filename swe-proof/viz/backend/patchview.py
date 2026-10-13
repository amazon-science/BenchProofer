# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Parse a unified diff (patch.diff) into structured files/hunks for rendering.

Pure-Python, no external diff library. Produces, per changed file, the list of
hunks with their lines tagged (context / added / removed) and old/new line
numbers — enough for a side-by-side or inline rendering with the diff's own
context lines, plus the file paths so the UI can offer "expand full file".
"""
from __future__ import annotations

import re

_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def changed_paths(diff: str) -> list[str]:
    paths = []
    for line in diff.splitlines():
        if line.startswith("+++ "):
            p = line[4:].strip()
            if p.startswith("b/"):
                p = p[2:]
            if p and p != "/dev/null":
                paths.append(p)
    return paths


def parse(diff: str) -> list[dict]:
    """Return [{old_path, new_path, hunks:[{header, lines:[{tag,old,new,text}]}]}]."""
    files: list[dict] = []
    cur: dict | None = None
    hunk: dict | None = None
    old_no = new_no = 0
    lines = (diff or "").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git"):
            cur = {"old_path": None, "new_path": None, "hunks": []}
            files.append(cur)
            hunk = None
        elif line.startswith("--- "):
            if cur is None:
                cur = {"old_path": None, "new_path": None, "hunks": []}
                files.append(cur)
            cur["old_path"] = _strip_ab(line[4:].strip())
        elif line.startswith("+++ "):
            if cur is None:
                cur = {"old_path": None, "new_path": None, "hunks": []}
                files.append(cur)
            cur["new_path"] = _strip_ab(line[4:].strip())
        elif line.startswith("@@"):
            m = _HUNK_RE.match(line)
            if m and cur is not None:
                old_no = int(m.group(1))
                new_no = int(m.group(3))
                hunk = {"header": (m.group(5) or "").strip(), "lines": []}
                cur["hunks"].append(hunk)
        elif hunk is not None and cur is not None:
            if line.startswith("+"):
                hunk["lines"].append({"tag": "add", "old": None, "new": new_no, "text": line[1:]})
                new_no += 1
            elif line.startswith("-"):
                hunk["lines"].append({"tag": "del", "old": old_no, "new": None, "text": line[1:]})
                old_no += 1
            elif line.startswith("\\"):  # "\ No newline at end of file"
                pass
            elif line.startswith(" ") or line == "":
                hunk["lines"].append({"tag": "ctx", "old": old_no, "new": new_no, "text": line[1:]})
                old_no += 1
                new_no += 1
            else:
                # unexpected line outside a recognized prefix; treat as context end
                hunk = None
        i += 1
    return files


def _strip_ab(p: str) -> str:
    if p.startswith(("a/", "b/")):
        return p[2:]
    return p


def stats(diff: str) -> dict:
    added = removed = 0
    for line in (diff or "").splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return {"added": added, "removed": removed, "files": len(changed_paths(diff))}
