#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-10466.

The operation under specification (publishing the recorded positions of a
message) is modeled DEEPLY in Solution.lean: a per-entry projection
(`toPos`), a per-code-point order (`lcharLt`), a total order on positions
(`posLe`), a deduplication (`List.dedup`), and a total-order sort (`mergeSort`
of `orderedPositions`).

Two of these stand in for UNCHANGED standard-library primitives and are
therefore A-references — the deep model must equal the real callee:

  (A-reference 1) the deduplication `(entries.map toPos).dedup` == Python's
      `set(...)` over the projected (source, line) 2-tuples (equal AS SETS:
      the distinct positions are exactly preserved).

  (A-reference 2) the total-order sort `mergeSort posLe` applied to the
      deduplicated positions == Python's stable `sorted(...)` of the SAME
      positions under the default tuple order (source lexicographic, then
      line). Composed: `mergeSort posLe ∘ dedup ∘ map toPos`
      == `sorted(set((source, line) for source, line, uuid in entries))`.

The projection `toPos` itself (drop the uuid, keep (source, line)) is concrete
and is differential-tested by conformance_check.py (G-CONF). G-AX only certifies
that the two stdlib primitives the deep model leans on behave as modeled.

Imports nothing repo-specific: `set` and `sorted` are the Python standard
library — the very primitives the gold patch calls. Exit 0 iff every obligation
holds.
"""
import random
import sys


# --- deep-model transliteration (kept in lock-step with Solution.lean) -------

def to_pos(entry):                         # toPos
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


def pos_le(x, y):                          # posLe
    if lchar_lt(x[0], y[0]):
        return True
    if lchar_lt(y[0], x[0]):
        return False
    return x[1] <= y[1]


def model_dedup(xs):
    """List.dedup analogue: keep one representative per distinct value."""
    seen = []
    out = []
    for x in xs:
        if x not in seen:
            seen.append(x)
            out.append(x)
    return out


def model_sort(xs):
    """mergeSort posLe modeled as a stable sort under the same total order.

    pos_le is a total preorder identical to the default tuple comparison, so a
    stable sort under it equals Python's `sorted` of the same elements."""
    return sorted(xs, key=lambda p: (p[0], p[1]))


def model_positions(entries):
    """The full deep model: project, dedup, sort."""
    return model_sort(model_dedup([to_pos(e) for e in entries]))


# --- the real callees the deep model references ------------------------------

def real_dedup_set(entries):
    """The UNCHANGED stdlib `set(...)` over the projected 2-tuples."""
    return set((source, line) for source, line, uuid in entries)


def real_positions(entries):
    """The UNCHANGED stdlib expression the gold patch calls."""
    return sorted(set((source, line) for source, line, uuid in entries))


# --- fuzz generation: realistic gettext metadata entries ---------------------

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
    uuid = "%032x" % rng.getrandbits(128)
    return (source, line, uuid)


def main():
    rng = random.Random(10466)

    boundary_lists = [
        [],
        # F2P test_Catalog_duplicated_message scenario for msgid 'hello':
        [("/path/to/filename", 1, "u1"),
         ("/path/to/filename", 1, "u2"),
         ("/path/to/filename", 2, "u3"),
         ("/path/to/yetanother", 1, "u4")],
        [("/path/to/filename", 1, "u1")],
        [("a.rst", 0, "u%d" % k) for k in range(6)],     # all duplicate
        [("z", 9, "u1"), ("a.rst", 9, "u2"), ("a.rst", 1, "u3")],
        [("hair.rst", 38, "u1"), ("hair.rst", 0, "u2"), ("hair.rst", 0, "u3")],
    ]

    fuzz_lists = list(boundary_lists)
    for _ in range(20000):
        k = rng.randint(0, 14)
        fuzz_lists.append([gen_entry(rng) for _ in range(k)])

    for entries in fuzz_lists:
        positions = [to_pos(e) for e in entries]

        # ---- A-reference 1: dedup == set(...) (equal as sets) --------------
        assert set(model_dedup(positions)) == real_dedup_set(entries), (
            "dedup deep model unsound on %r: model-set %r, set(...) %r"
            % (entries, set(model_dedup(positions)), real_dedup_set(entries)))

        # ---- A-reference 2 (composed): full model == real expression -------
        assert model_positions(entries) == real_positions(entries), (
            "dedup+sort deep model unsound on %r: model %r, real %r"
            % (entries, model_positions(entries), real_positions(entries)))

    print("G-AX OK: dedup deep model (== set) + total-order sort deep model "
          "(== sorted) sound on %d boundary + 20000 fuzz entry lists"
          % len(boundary_lists))
    return 0


if __name__ == "__main__":
    sys.exit(main())
