#!/usr/bin/env python
"""G-CONF: differential conformance for pytest-dev__pytest-10356.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_inheritedMarks` skeleton and diffs it against the REAL patched
callee `_pytest.mark.structures.get_unpacked_marks` over a discrete catalogue of
inheritance shapes plus >=1e5 randomized class hierarchies.

Modeled function: `get_unpacked_marks(obj, *, consider_mro)` for the class case
(`isinstance(obj, type)` is true) — exactly the branch the gold patch rewrites.
The real callee gathers, in MRO order, each class's OWN stored `pytestmark`
entry (`cls.__dict__.get("pytestmark", [])`), flattening list/single forms, and
normalizes the result. When `consider_mro` is false it gathers only the class's
own entry.

Bridge (mapping.md):
  * a Lean `hierarchy : List ClassMarks` <-> the sequence
    `[cls.__dict__.get("pytestmark", []) for cls in obj.__mro__]`;
  * `ClassMarks.many xs` <-> a stored Python `list` of marks; `ClassMarks.one m`
    <-> a stored bare mark (non-list);
  * `wholeHierarchy : Bool` <-> the `consider_mro` keyword;
  * a Lean `Mark {name, args}` <-> a real `Mark` compared on `(name, args)`.
The Lean result `List Mark` is compared element-for-element (by name+args)
against the real callee's returned list.

Exit 0 iff zero disagreements. stdlib only (plus the in-container pytest). Pinned
seed.
"""
import random
import sys

SEED = 20240627
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_inheritedMarks (post-patch R/I leg) -----
#
# `hierarchy` is a list of stored entries, one per class in MRO order. Each entry
# is either a Python list of marks (ClassMarks.many) or a single bare mark
# (ClassMarks.one). `flattenClassMarks`: a list passes through; a bare mark
# becomes [mark].

def flatten_entry(entry):
    if isinstance(entry, list):
        return list(entry)
    return [entry]


def shadow_inherited_marks(hierarchy, whole_hierarchy):
    """Transliteration of problem_spec / implementation_inheritedMarks."""
    if not whole_hierarchy:
        mark_lists = [hierarchy[0] if hierarchy else []]
    else:
        mark_lists = hierarchy
    mark_list = []
    for item in mark_lists:
        mark_list.extend(flatten_entry(item))
    return mark_list


# ---- real callee observation ------------------------------------------------

def key(mark):
    """Compare marks structurally (the modeled observable: name + args)."""
    return (mark.name, tuple(mark.args))


def main():
    from _pytest.mark.structures import get_unpacked_marks, Mark

    # build distinct real Mark objects via the private constructor.
    def mk(name):
        return Mark(name, (), {}, _ispytest=True)

    POOL = [mk(n) for n in ("a", "b", "c", "d", "e", "f", "foo", "bar")]

    rng = random.Random(SEED)

    def rand_marklist():
        """A stored `pytestmark` value: list of marks, or (rarely) a bare mark."""
        roll = rng.random()
        if roll < 0.15:
            return rng.choice(POOL)            # bare single mark (ClassMarks.one)
        k = rng.randint(0, 3)
        return [rng.choice(POOL) for _ in range(k)]  # list (ClassMarks.many)

    disagreements = 0
    checked = 0

    def build_class_chain(entries):
        """Create a single-inheritance chain of classes whose MRO carries the
        given stored entries (entries[0] = most-derived). Returns the leaf class
        and the list of stored entries aligned to leaf.__mro__ (which appends the
        implicit trailing `object`, storing no pytestmark)."""
        # Build from the base up so each class's own __dict__ holds its entry.
        klass = object
        for entry in reversed(entries):
            klass = type("C", (klass,), {"pytestmark": entry})
        return klass

    def run_case(entries, whole):
        nonlocal disagreements, checked
        leaf = build_class_chain(entries)
        # hierarchy aligned to the REAL mro: each class's OWN stored entry,
        # default [] (this is exactly what the real callee reads).
        hierarchy = [cls.__dict__.get("pytestmark", []) for cls in leaf.__mro__]
        got = list(get_unpacked_marks(leaf, consider_mro=whole))
        exp = shadow_inherited_marks(hierarchy, whole)
        checked += 1
        if [key(m) for m in got] != [key(m) for m in exp]:
            disagreements_local = True
            return leaf, got, exp, hierarchy
        return None

    # discrete catalogue: chain depths 1..4, both modes, incl. the issue's
    # multi-labelled-ancestor shape.
    discrete = [
        [["foo"]],
        [[], ["bar"]],
        [["c"], ["a"], ["b"]],            # the reported C(A,B) case, linearized
        [["a", "b"], ["c"]],
        [[], [], ["d"]],
        [["a"], [], ["b"], ["c"]],
    ]
    def resolve(entries):
        return [[mk(n) for n in lst] for lst in entries]

    cases = []
    for spec in discrete:
        for whole in (True, False):
            cases.append((resolve(spec), whole))

    for _ in range(N_RANDOM):
        depth = rng.randint(1, 5)
        entries = [rand_marklist() for _ in range(depth)]
        whole = rng.random() < 0.5
        cases.append((entries, whole))

    for entries, whole in cases:
        res = run_case(entries, whole)
        if res is not None:
            disagreements += 1
            if disagreements <= 5:
                leaf, got, exp, hierarchy = res
                print(f"MISMATCH whole={whole} hierarchy={hierarchy!r}: "
                      f"real={[key(m) for m in got]} shadow={[key(m) for m in exp]}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
