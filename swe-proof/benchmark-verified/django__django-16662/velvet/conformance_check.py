#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16662 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's impl region (`orderImportLines`) transliterated to
              Python over the real repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, code point ↔ `ord`). It is an
              INDEPENDENT from-scratch transliteration: a hand-written stable
              merge sort under the boolean comparator `keyLe`, with from-scratch
              `firstTok`/`moduleTok`/`lcharLe`. It does NOT call Python's
              `sorted` or `str.split` — those are the A-reference primitives the
              deep model leans on (validated separately by axiom_check.py /
              G-AX). The R/I leg under test here is the CHANGED composite-key
              logic: group whole-module lines ahead of qualified lines, then by
              module token.
  * ORACLE  — patch.diff's behaviour: the gold hunk's exact sort expression,
              `sorted(imports, key=lambda i: (i.split()[0] == "from",
              i.split()[1]))`, run with Python's stdlib `sorted` + `str.split`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample (e.g. a wrong grouping direction or
tie-break in the transliterated key).

Runs in-container, stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 16662
N_FUZZ = 100_000


# --- SHADOW: from-scratch transliteration of Solution.lean's impl ------------

def first_tok(line):                       # firstTok
    out = []
    for c in line:
        if c == " ":
            break
        out.append(c)
    return "".join(out)


def after_first(line):                     # afterFirst
    for i, c in enumerate(line):
        if c == " ":
            return line[i + 1:]
    return ""


def module_tok(line):                      # moduleTok
    return first_tok(after_first(line))


def is_qualified(line):                    # isQualified
    return first_tok(line) == "from"


def lchar_le(a, b):                        # lcharLe (per code point, total)
    i = 0
    while True:
        if i >= len(a):
            return True
        if i >= len(b):
            return False
        ca, cb = ord(a[i]), ord(b[i])
        if ca < cb:
            return True
        if cb < ca:
            return False
        i += 1


def key_le(x, y):                          # keyLe
    if is_qualified(x) == is_qualified(y):
        return lchar_le(module_tok(x), module_tok(y))
    return is_qualified(x) is False


def stable_merge_sort(xs):
    """Stable sort under the boolean comparator key_le — mirrors Lean
    `List.mergeSort keyLe`. In the merge, the left element is taken when
    `key_le(left, right)` holds, preserving original order on ties."""
    if len(xs) <= 1:
        return list(xs)
    mid = len(xs) // 2
    left = stable_merge_sort(xs[:mid])
    right = stable_merge_sort(xs[mid:])
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key_le(left[i], right[j]):
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def shadow_sort(lines):
    return stable_merge_sort(list(lines))


# --- ORACLE: the gold patch's exact sort expression -------------------------

def oracle_sort(lines):
    return sorted(lines, key=lambda i: (i.split()[0] == "from", i.split()[1]))


# --- fuzz generation ---------------------------------------------------------

_MODULES = [
    "datetime", "time", "os", "sys", "re", "uuid", "json", "abc", "zoneinfo",
    "pathlib", "decimal", "collections", "functools", "itertools",
    "django.db", "django.conf", "django.utils.timezone", "django.core",
    "django.db.models", "myapp.models", "a", "b", "z", "aa", "ab", "Z", "A",
]
_OBJECTS = ["models", "migrations", "settings", "x", "y", "Foo", "Bar"]


def gen_line(rng):
    mod = rng.choice(_MODULES)
    if rng.random() < 0.5:
        return "import %s" % mod
    objs = ", ".join(rng.sample(_OBJECTS, rng.randint(1, 3)))
    return "from %s import %s" % (mod, objs)


def fuzz_lists(n, rng):
    # boundary cases first (plan §4.1 step 4): the exact F2P scenario + stress
    yield []
    yield ["import datetime", "from django.db import migrations, models",
           "import time"]
    yield ["from django.db import migrations, models", "import datetime",
           "import time"]
    yield ["import time", "import datetime",
           "from django.db import migrations, models"]
    yield ["from a import x", "import a", "from a import y", "import a"]
    yield ["from z import a", "from a import z", "import z", "import a"]
    yield ["import datetime", "import time",
           "from django.db import migrations, models"]
    for _ in range(n):
        k = rng.randint(0, 12)
        yield [gen_line(rng) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for lst in fuzz_lists(N_FUZZ, rng):
        count += 1
        shadow = shadow_sort(lst)
        oracle = oracle_sort(lst)
        if shadow != oracle:
            disagreements.append((lst, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for lst, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (lst, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of orderImportLines agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
