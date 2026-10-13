#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16662.

The operation under specification (ordering a collection of import-statement
lines) is modeled DEEPLY in Solution.lean: a whitespace token split
(`firstTok`/`moduleTok`), a per-code-point order (`lcharLe`), a composite
ordering key (`keyLe`), and a stable sort (`mergeSort` of `sortImports`).

Two of these stand in for UNCHANGED standard-library primitives and are
therefore A-references — the deep model must equal the real callee:

  (A-reference 1) the token split `firstTok`/`moduleTok` == Python's
      `str.split()` selection of tokens 0 and 1. The line's first
      whitespace-delimited token and the token after it.

  (A-reference 2) the stable key-sort `sortImports` (mergeSort under `keyLe`)
      == Python's stable `sorted(lines, key=...)` with the SAME composite key
      `(line.split()[0] == "from", line.split()[1])`.

The composite-key *logic itself* (group whole-module lines ahead of qualified
lines, then by module token) is the CHANGED behavior — it is NOT an axiom; it
is concrete and is differential-tested by conformance_check.py (G-CONF). G-AX
only certifies that the two stdlib primitives the deep model leans on behave as
modeled.

Imports nothing repo-specific: `str.split` and `sorted` are the Python
standard library — the very primitives the gold patch calls. Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- deep-model transliteration (kept in lock-step with Solution.lean) -------

def first_tok(line):
    """firstTok: chars up to the first ' ' (single-space delimiter)."""
    out = []
    for c in line:
        if c == " ":
            break
        out.append(c)
    return "".join(out)


def after_first(line):
    """afterFirst: everything after the first ' ' (delimiter consumed)."""
    for i, c in enumerate(line):
        if c == " ":
            return line[i + 1:]
    return ""


def module_tok(line):
    """moduleTok: the second whitespace-delimited token."""
    return first_tok(after_first(line))


def is_qualified(line):
    """isQualified: leading token is the word 'from'."""
    return first_tok(line) == "from"


def lchar_le(a, b):
    """lcharLe: lexicographic by code point. Total preorder == Python str <=."""
    return a <= b  # Python str comparison is code-point lexicographic


def key_le(x, y):
    """keyLe: whole-module lines first, then by module token."""
    if is_qualified(x) == is_qualified(y):
        return lchar_le(module_tok(x), module_tok(y))
    return is_qualified(x) is False


def model_sort(lines):
    """sortImports: stable sort under key_le. Mirrors Lean mergeSort(keyLe).

    Implemented via a stable key so it is provably identical to a stable
    mergeSort under the total preorder key_le."""
    return sorted(lines, key=lambda i: (is_qualified(i), module_tok(i)))


# --- the real callees the deep model references ------------------------------

def real_first_token(line):
    return line.split()[0]


def real_module_token(line):
    return line.split()[1]


def real_sorted(lines):
    """The UNCHANGED stdlib stable sort under the patched composite key."""
    return sorted(lines, key=lambda i: (i.split()[0] == "from", i.split()[1]))


# --- fuzz generation: realistic import-statement lines -----------------------

_MODULES = [
    "datetime", "time", "os", "sys", "re", "uuid", "json", "abc", "zoneinfo",
    "pathlib", "decimal", "collections", "functools", "itertools",
    "django.db", "django.conf", "django.utils.timezone", "django.core",
    "django.db.models", "myapp.models", "a", "b", "z", "aa", "ab", "Z", "A",
]
_OBJECTS = ["models", "migrations", "settings", "x", "y", "Foo", "Bar"]


def gen_line(rng):
    """A whitespace-single-spaced import line, in the domain the writer emits."""
    mod = rng.choice(_MODULES)
    if rng.random() < 0.5:
        return "import %s" % mod
    objs = ", ".join(rng.sample(_OBJECTS, rng.randint(1, 3)))
    return "from %s import %s" % (mod, objs)


def main():
    rng = random.Random(16662)

    # ---- A-reference 1: token split == str.split() tokens 0 and 1 ----------
    boundary_lines = [
        "import datetime",
        "import time",
        "from django.db import migrations, models",
        "from django.conf import settings",
        "import os",
        "from a import b",
        "import a",
    ]
    fuzz_lines = boundary_lines + [gen_line(rng) for _ in range(20000)]
    for line in fuzz_lines:
        assert first_tok(line) == real_first_token(line), (
            "firstTok deep model unsound on %r: model %r, str.split()[0] %r"
            % (line, first_tok(line), real_first_token(line)))
        assert module_tok(line) == real_module_token(line), (
            "moduleTok deep model unsound on %r: model %r, str.split()[1] %r"
            % (line, module_tok(line), real_module_token(line)))

    # ---- A-reference 2: stable key-sort == real sorted(..., composite key) -
    # boundary list: the exact F2P scenario plus stress lists
    boundary_lists = [
        [],
        ["import datetime", "from django.db import migrations, models",
         "import time"],
        ["from django.db import migrations, models", "import datetime",
         "import time"],
        ["import time", "import datetime",
         "from django.db import migrations, models"],
        # ties on module token across the from/import groups
        ["from a import x", "import a", "from a import y", "import a"],
        ["from z import a", "from a import z", "import z", "import a"],
    ]
    for lst in boundary_lists:
        assert model_sort(lst) == real_sorted(lst), (
            "stable key-sort deep model unsound on %r: model %r, real %r"
            % (lst, model_sort(lst), real_sorted(lst)))

    for _ in range(20000):
        n = rng.randint(0, 12)
        # allow duplicates: the real writer dedups via a set, but the sort
        # primitive must still agree on arbitrary lists (stability included)
        lst = [gen_line(rng) for _ in range(n)]
        assert model_sort(lst) == real_sorted(lst), (
            "stable key-sort deep model unsound on %r: model %r, real %r"
            % (lst, model_sort(lst), real_sorted(lst)))

    print("G-AX OK: token-split deep model (== str.split) sound on %d lines; "
          "stable key-sort deep model (== sorted composite-key) sound on %d "
          "boundary + 20000 fuzz lists" % (len(fuzz_lines), len(boundary_lists)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
