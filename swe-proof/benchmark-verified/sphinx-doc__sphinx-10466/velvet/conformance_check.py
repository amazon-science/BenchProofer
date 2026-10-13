#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10466 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's impl region (`publishPositions`) transliterated to
              Python over the real repo types (`List[Tuple[str, int, str]]`), via
              the mapping.md bijection (`List Char` ↔ `str`, `Int` ↔ `int`). It
              is an INDEPENDENT from-scratch transliteration: a hand-written
              `to_pos` projection, a from-scratch set-based dedup, and a
              hand-written stable merge sort under the boolean comparator
              `pos_le`. It does NOT call Python's `sorted` or `set` (those are
              the A-reference primitives the deep model leans on, validated
              separately by axiom_check.py / G-AX). The R/I leg under test here
              is the CHANGED behavior: project each entry to (source, line),
              collapse coincident positions, and list the survivors ascending.
  * ORACLE  — patch.diff's behaviour: the gold hunk's exact expression,
              `sorted(set((source, line) for source, line, uuid in entries))`,
              run with Python's stdlib `sorted` + `set`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample (e.g. a wrong projection, a missing
dedup, or a wrong sort order in the transliterated key).

Runs in-container, stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 10466
N_FUZZ = 100_000


# --- SHADOW: from-scratch transliteration of Solution.lean's impl ------------

def to_pos(entry):                         # toPos: drop the identity tag
    source, line, _uuid = entry
    return (source, line)


def lchar_lt(a, b):                        # lcharLt (strict, per code point)
    i = 0
    while True:
        if i >= len(a) and i >= len(b):
            return False
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


def pos_le(x, y):                          # posLe (source lexicographic, then line)
    if lchar_lt(x[0], y[0]):
        return True
    if lchar_lt(y[0], x[0]):
        return False
    return x[1] <= y[1]


def model_dedup(xs):
    """List.dedup analogue: keep one representative per distinct value.

    Implemented from scratch (no `set` literal as a collapsing primitive in the
    final-result sense): walk left-to-right, keep first occurrences. The final
    result is order-canonicalised by the sort below, so any dedup order yields
    the same answer; first-occurrence is the simplest faithful choice."""
    seen = []
    out = []
    for x in xs:
        if x not in seen:
            seen.append(x)
            out.append(x)
    return out


def stable_merge_sort(xs):
    """Stable sort under the boolean comparator pos_le — mirrors Lean
    `List.mergeSort posLe`. Input is already deduplicated (distinct positions),
    so no ties arise; stability is immaterial but preserved."""
    if len(xs) <= 1:
        return list(xs)
    mid = len(xs) // 2
    left = stable_merge_sort(xs[:mid])
    right = stable_merge_sort(xs[mid:])
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if pos_le(left[i], right[j]):
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def shadow_positions(entries):
    return stable_merge_sort(model_dedup([to_pos(e) for e in entries]))


# --- ORACLE: the gold patch's exact expression ------------------------------

def oracle_positions(entries):
    return sorted(set((source, line) for source, line, uuid in entries))


# --- fuzz generation ---------------------------------------------------------

_SOURCES = [
    "../../manual/modeling/hair.rst",
    "../../manual/modeling/metas/properties.rst",
    "../../manual/physics/dynamic_paint/brush.rst",
    "../../manual/physics/dynamic_paint/canvas.rst",
    "/path/to/filename",
    "/path/to/yetanother",
    "index.rst", "a.rst", "b.rst", "Z.rst", "A.rst", "", "z",
]
_LINES = [0, 1, 2, 38, 92, 96, 121, 125, 153, 157, -1]


def gen_entry(rng):
    source = rng.choice(_SOURCES)
    line = rng.choice(_LINES)
    # uuids are distinct identity tags: many entries share (source, line) but
    # differ in uuid — exactly the duplication the issue reports.
    uuid = "%032x" % rng.getrandbits(128)
    return (source, line, uuid)


def fuzz_lists(n, rng):
    # boundary cases first (plan §4.1 step 4): the exact F2P scenario + stress.
    yield []
    # F2P test_Catalog_duplicated_message scenario for msgid 'hello':
    yield [
        ("/path/to/filename", 1, "u1"),
        ("/path/to/filename", 1, "u2"),   # duplicate (source,line)
        ("/path/to/filename", 2, "u3"),
        ("/path/to/yetanother", 1, "u4"),
    ]
    # single entry; all-duplicate; reverse-sorted distinct
    yield [("/path/to/filename", 1, "u1")]
    yield [("a.rst", 0, "u%d" % k) for k in range(6)]
    yield [("z", 9, "u1"), ("a.rst", 9, "u2"), ("a.rst", 1, "u3")]
    # ties on source, distinct lines (secondary key exercised)
    yield [("hair.rst", 38, "u1"), ("hair.rst", 0, "u2"), ("hair.rst", 0, "u3")]
    for _ in range(n):
        k = rng.randint(0, 14)
        yield [gen_entry(rng) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for lst in fuzz_lists(N_FUZZ, rng):
        count += 1
        shadow = shadow_positions(lst)
        oracle = oracle_positions(lst)
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
    print("G-CONF OK: R/I shadow of publishPositions agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
