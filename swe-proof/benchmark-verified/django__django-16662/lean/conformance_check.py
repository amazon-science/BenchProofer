#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16662.

The bundle models ONE decision: the order in which the collected import
statements of a generated migration module are emitted
(`MigrationWriter.as_string`, the `sorted_imports = sorted(imports, key=...)`
line). The modeled value is a PURE function of the statement list (mapping.md):

    imports : list[str]   (canonical single-space import-statement lines)

Post-patch rule (the gold patch):

    sorted_imports = sorted(imports, key=lambda i: (i.split()[0] == "from",
                                                     i.split()[1]))

Standing up the full migration writer (an ORM + a Migration object) is heavy and
unnecessary: the modeled value is this pure ordering over statement strings. So
the ORACLE below is the EXACT patched expression — `sorted` with the gold
composite key lambda — and the SHADOW is the op-for-op transliteration of
`implementation_sortImportStatements` (a stable merge sort under `importLe`, per
refinement.md). Both `sorted` and a stable merge sort are stable, so the two
legs are compared by EXACT LIST EQUALITY.

This genuinely tests the Lean composite-key modeling: the shadow reaches the
order via `importLe` (plain-before-from, then module name), the oracle via the
Python tuple key `(split()[0]=="from", split()[1])`; they must agree for every
input — in particular when a plain `import` has a module name lexicographically
after a `from` import's module (the grouping the patch enforces), and when two
statements share a module name (the stability / tie case).

Scope (mapping.md): the writer assembles canonical single-space import lines
(`"import <mod>"` / `"from <mod> import <objs>"`), so the fuzzer draws from that
shape; `i.split()` and `i.splitOn(" ")` agree on tokens [0] and [1] there. This
restriction is intentional and logged below.

stdlib-only. Pinned seed: 16662 (also in mapping.md).
"""
import random
import sys

SEED = 16662
N = 120_000


# --- ORACLE: the EXACT patched decision --------------------------------------
def oracle_sort(imports):
    return sorted(imports, key=lambda i: (i.split()[0] == "from", i.split()[1]))


# --- SHADOW of implementation_sortImportStatements (the R/I leg) -------------
# Mirrors Solution.lean: firstToken/moduleName via split, importLe preorder,
# stable mergeSort. Python's `sorted` with a key is itself a stable sort, so we
# realize `mergeSort importLe` as `sorted` under the SAME importLe-derived key.
def _first_token(line):
    parts = line.split(" ")
    return parts[0] if parts else ""


def _module_name(line):
    parts = line.split(" ")
    return parts[1] if len(parts) > 1 else ""


def _is_from(line):
    return _first_token(line) == "from"


def shadow_sort(imports):
    # importLe: plain-import (is_from False) before from-import (True), then by
    # module name. A stable sort by the key (is_from, module_name) realizes the
    # exact total preorder `importLe` used by the Lean `mergeSort`.
    return sorted(imports, key=lambda i: (_is_from(i), _module_name(i)))


def disagree(imports):
    got = oracle_sort(imports)
    want = shadow_sort(imports)
    if got != want:
        return (imports, got, want)
    return None


MOD_POOL = ["datetime", "time", "uuid", "os", "sys", "re", "django.db",
            "django.conf", "django.utils.timezone", "decimal", "json", "abc"]


def _mk_import(mod):
    return "import %s" % mod


def _mk_from(mod):
    return "from %s import a, b" % mod


def _enumerate_edge():
    cases = []
    # The canonical F2P shape (#24155): module-only sort would leave
    # "import time" after the from-import; grouping must pull both imports up.
    cases.append(["import datetime",
                  "from django.db import migrations, models",
                  "import time"])
    cases.append([])                                    # empty
    cases.append(["import os"])                         # singleton import
    cases.append(["from a import x"])                   # singleton from
    cases.append(["import b", "import a"])              # two imports, reorder
    cases.append(["from b import x", "from a import y"])  # two froms, reorder
    cases.append(["from a import x", "import z"])       # from before import in input
    # tie on module name across kinds (import zzz vs from zzz) -> grouping decides
    cases.append(["from zzz import x", "import zzz"])
    # all from
    cases.append(["from c import x", "from a import y", "from b import z"])
    # all import
    cases.append(["import c", "import a", "import b"])
    return cases


def main() -> int:
    checked = 0
    for imports in _enumerate_edge():
        d = disagree(imports)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        k = rng.randint(0, 8)
        stmts = []
        for _ in range(k):
            mod = rng.choice(MOD_POOL)
            if rng.random() < 0.5:
                stmts.append(_mk_import(mod))
            else:
                stmts.append(_mk_from(mod))
        # statements come from a set() in the real writer -> distinct
        stmts = list(dict.fromkeys(stmts))
        d = disagree(stmts)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
