#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20154 (nagini).

SHADOW — the impl region of `model.py`, copied VERBATIM below with only the
contract calls removed (`Requires`, `Ensures`, `Invariant`, `MustTerminate` and
the `# invariants-start/-end` markers).  The `@Pure` helper `state_at` the
region's postcondition depends on is copied too, minus its contracts.  No
restructuring, no renaming: `gather_walk` still builds `result` by advancing the
live `work` value one step at a time and appending a by-value `snap` per step,
and `state_at(i)` is still `i + 1`.  This bundle's model uses plain
`List[int]`/`append`, so no `PSeq`/`ToSeq` shim is needed, and it axiomatizes
NOTHING (`# axioms-start` region is empty, no `@ContractOnly` callee), so there
is no axiom stub to redirect at a repo function.

ORACLE — the REAL patched repo function, CALLED, not transliterated:
`sympy.utilities.iterables.partitions` (`sympy/utilities/iterables.py:1696` at
base_commit bdb49c4abfb35554a3c8ce761696ffff3bb837fe), gathered into a list.
mapping.md §1 binds the model to `list(partitions(...))` — the act of GATHERING
the generator, which is what every F2P assertion does — and the gold patch's
whole behavioural content is the `yield ms` -> `yield ms.copy()` at
iterables.py:1805,1807,1845,1847.  The gate applies patch.diff to /testbed and
sets PYTHONPATH before this script runs, so the imported generator is the
patched one; nothing about it is reimplemented here.  (The velvet sibling
abstracts the gather to a per-step index list; the lean sibling calls the real
generator.  This check calls the real generator, and additionally derives the
abstraction function from the generator's own observed output rather than
assuming it — see the bridge below.)

TYPE BRIDGE (mapping.md §2, inverted).  Concrete side: the gathered list
`G = list(islice(partitions(n, m, k, size), limit))`, whose entries are the
records handed out (a partition `dict`, or a `(M, dict)` pair when `size=True`).
Abstract side: `steps : int` and `List[int]`.

  * `steps` <- the number of records the walk performs, derived INDEPENDENTLY of
    what the gather hands out, by snapshotting each yield ourselves at consume
    time: `T = [copy of y for y in islice(partitions(...), limit)]`.  `T` is the
    genuine per-step history; it is patch-independent (the enumeration algorithm
    is untouched by the patch — only what the yields hand out changed), so it is
    a legitimate ruler for both the step count and the per-step values.
    `steps = len(T)`.  Deriving `steps` from `T` and not from `len(G)` is what
    keeps the `len(Result()) == steps` leg of the postcondition under test
    instead of trivially true.
  * `G[k] : record` -> `int`: mapping.md §2 abstracts "each yielded partition's
    per-step value" to `state_at(i) == i + 1`, i.e. a record is abstracted to
    (the index of the step whose state it holds) + 1.  So
    `alpha(G)[k] = 1 + j` where `j` is the unique step index with
    `G[k] == T[j]`.  `T`'s entries are pairwise distinct (asserted per input, so
    a violation is reported rather than silently absorbed), which makes `j`
    unique and `alpha` well defined.  A record matching no step at all
    abstracts to the sentinel `0`, which is outside `state_at`'s range and
    therefore always disagrees.

  This abstraction is what makes the check refutable rather than decorative.
  Under the patched generator each `G[k]` is an independent snapshot equal to
  `T[k]`, so `alpha(G) == [1, .., steps]` and the shadow must match.  Under the
  PRE-patch generator every `G[k]` aliases the single live `ms` and reads back
  as the last gathered state, so `alpha(G) == [steps, .., steps]` (or the
  sentinel for `size=True`, where the tuple's `M` no longer matches its dict) —
  a length->=2 disagreement against the shadow's `[1, .., steps]`.  The bridge
  additionally treats object-identity aliasing among the gathered records as a
  disagreement in its own right (mapping.md §2's `ms.copy()` row: the gathered
  record must be a FRESH object isolated from later mutation of the source), so
  the independence leg is checked and not just its value shadow.  This was
  negative-controlled: run against a pre-patch replica of the generator the
  check reports disagreements and exits 1.

INPUT DOMAIN — every input satisfies the model's `Requires(steps >= 0)`
(`steps = len(T) >= 0` by construction; `MustTerminate` is an obligation, not a
value constraint), and every generated argument tuple is one the real generator
accepts.  `limit` (an `itertools.islice` bound on the gather) is what reaches
`steps == 0`: the real generator always yields at least once, so a zero-step
gather of it is exactly `limit=0`; `limit` also exercises partial gathers.
Both impl branches are covered: the `while i < steps` body is taken zero times
(`limit=0`) and many times.  Boundary block first — every argument shape the
F2P `test_partitions` asserts on (`partitions(0)`, `partitions(1, 0)`,
`partitions(6, 2, 2)`, `(6, 2, None)`, `(6, None, 2)`, `(6, 2, 0)`,
`k=2`/`k=3`/`k=4,m=3`/`m=2`/`k=3` gathers, `S(3)` included when sympy's `S`
imports), each with `size` False and True, and each of the real function's
branches (the degenerate `yield {}` early return, the first yield, the loop
yield, the `if not keys: return` exhaustion path) taken at least once — then
exhaustive enumeration of the finite grid n in 0..12 x m,k in {None} u 0..12 x
size in {False, True} (5096 argument tuples, full gathers), then seeded fuzz
over a wider grid (n <= 24, with random `limit`) to fill the count.  The modeled
input space is infinite (`steps` is unbounded), so the exhaustive grid is a
sub-block, not a completeness claim.

Total: >= 100000 inputs.  Pinned seed: SEED = 20154 (recorded in mapping.md
§ G-CONF).  stdlib only (hypothesis not needed: the generator is enumerated
directly).  Exit 0 iff zero disagreements; on disagreement the input and both
sides are printed and the exit status is 1.
"""
import itertools
import json
import random
import sys

SEED = 20154
N_TOTAL = 100000

# ---------------------------------------------------------------------------
# SHADOW: model.py's `# pure-start` helper + `# impl-start` .. `# impl-end`
# region, verbatim, contracts stripped.  Do not "simplify" this code.
# ---------------------------------------------------------------------------


def state_at(i):
    """The working value recorded for step i. Successive steps genuinely change
    it, so the per-step values are pairwise distinct; modelled as the
    strictly-increasing identity i+1 so step i differs from step j."""
    return i + 1


def gather_walk(steps):
    result = []  # type: List[int]
    # The live working value the walk advances IN PLACE across steps: it starts
    # before the first step and is incremented one step at a time (never
    # recomputed from scratch), exactly as the enumerator advances its single
    # working record from one state to the next.
    work = 0
    i = 0
    while i < steps:
        # Advance the working state in place by one step (the enumerator's
        # mutation step): the record now holds the state for step i.
        work = work + 1
        # Hand out an INDEPENDENT snapshot of the working state (the snapshot
        # step): the current value is recorded by value, so later mutations of
        # the working state leave this gathered record untouched.
        snap = work
        result.append(snap)
        i = i + 1
    return result


# ---------------------------------------------------------------------------
# Type bridge (mapping.md section 2, inverted)
# ---------------------------------------------------------------------------

ALIASED = "aliased"      # gathered records are not independent objects
UNMAPPABLE = 0           # outside state_at's range (state_at(i) >= 1)


def _part_of(rec, size):
    """The partition dict inside a yielded record."""
    return rec[1] if size else rec


def _snapshot(rec, size):
    """Copy a yielded record at consume time: the per-step ground truth, taken
    the way the F2P tests take it ([p.copy() for p in partitions(...)]).  This
    is patch-independent -- the enumeration algorithm is untouched by the gold
    patch -- so it is a legitimate ruler for both sides."""
    if size:
        return (rec[0], dict(rec[1]))
    return dict(rec)


def _key(snap, size):
    """Hashable canonical form of a snapshotted record."""
    if size:
        return (snap[0], tuple(sorted(snap[1].items())))
    return tuple(sorted(snap.items()))


def truth_history(partitions, n, m, k, size, limit):
    """steps and the genuine per-step states: snapshot each yield ourselves."""
    return [_snapshot(rec, size) for rec in
            itertools.islice(partitions(n, m=m, k=k, size=size), limit)]


def real_gather(partitions, n, m, k, size, limit):
    """The oracle: gather the REAL patched generator, exactly as the F2P tests'
    list(partitions(...)) does (bounded by limit so a zero-step gather is
    reachable)."""
    return list(itertools.islice(partitions(n, m=m, k=k, size=size), limit))


def abstract(gathered, truth, size):
    """alpha: gathered records -> List[int] under mapping.md section 2.

    Record k abstracts to 1 + (the step whose state it holds).  Returns
    ALIASED when the gathered records are not pairwise-independent objects (the
    modeled defect, mapping.md section 2's ms.copy() row), and the sentinel
    UNMAPPABLE for a record that holds no step's state at all."""
    parts = [_part_of(rec, size) for rec in gathered]
    if len(parts) > 1 and len({id(p) for p in parts}) != len(parts):
        return ALIASED
    index = {}
    for j, snap in enumerate(truth):
        index[_key(snap, size)] = j
    out = []
    for rec in gathered:
        j = index.get(_key(_snapshot(rec, size), size))
        out.append(UNMAPPABLE if j is None else state_at(j))
    return out


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

FULL = None  # gather every step the generator performs


def boundary_inputs():
    """Every F2P argument shape, each real-function branch, and both impl
    branches (loop body taken zero times via limit=0, and many times)."""
    argsets = [
        (0, None, None),        # degenerate early return: yield {} / (0, {})
        (1, 0, None),           # m < 1 -> degenerate
        (6, 2, 2),              # m*k < n -> degenerate
        (6, 2, 0),              # k < 1 -> degenerate
        (6, 2, None),           # non-degenerate, m limited
        (6, None, 2),           # the docstring/F2P example: 4 partitions
        (6, None, 3),           # F2P: 7 partitions
        (8, 3, 4),              # F2P: partitions(8, k=4, m=3)
        (3, 2, None),           # F2P: partitions(S(3), m=2)
        (4, None, 3),           # F2P: partitions(4, k=3)
        (4, None, None),        # F2P: partitions(4)
        (1, None, None),        # single-step walk
        (2, None, None),
        (1, 1, 1),
        (5, 1, None),           # m == 1: single partition
        (5, None, 1),           # k == 1: single partition
        (12, 3, 4),             # exhaustion path (`if not keys: return`)
        (13, 2, 7),
        (-1, None, None),       # n <= 0 -> degenerate
        (0, 0, 0),
    ]
    out = []
    for (n, m, k) in argsets:
        for size in (False, True):
            out.append((n, m, k, size, FULL))
            out.append((n, m, k, size, 0))     # zero-step gather: steps == 0
            out.append((n, m, k, size, 1))     # single-step gather
            out.append((n, m, k, size, 3))
    return out


def exhaustive_inputs():
    """The finite grid n in 0..12 x m,k in {None} u 0..12 x size in {F, T},
    full gathers: 5096 argument tuples enumerated exhaustively."""
    choices = [None] + list(range(0, 13))
    out = []
    for n in range(0, 13):
        for m in choices:
            for k in choices:
                for size in (False, True):
                    out.append((n, m, k, size, FULL))
    return out


def fuzz_input(rng):
    n = rng.randint(0, 24)
    m = rng.choice([None] + list(range(0, 10)))
    k = rng.choice([None] + list(range(0, 10)))
    size = rng.random() < 0.5
    r = rng.random()
    if r < 0.70:
        limit = FULL
    elif r < 0.80:
        limit = 0
    else:
        limit = rng.randint(1, 12)
    return (n, m, k, size, limit)


# ---------------------------------------------------------------------------
# Differential comparison
# ---------------------------------------------------------------------------


def check_one(partitions, inp):
    """Returns None on agreement, else a human-readable disagreement report."""
    (n, m, k, size, limit) = inp
    truth = truth_history(partitions, n, m, k, size, limit)

    # Bridge well-formedness: the per-step states must be pairwise distinct for
    # alpha to be well defined.  This is a FINDING about the abstraction if it
    # ever fails, not something to route around, so report it.
    keys = [_key(s, size) for s in truth]
    if len(set(keys)) != len(keys):
        return ("BRIDGE VIOLATION: per-step history not pairwise distinct\n"
                "  input=%r\n  truth=%r" % (inp, truth))

    steps = len(truth)                       # steps derived from the ruler
    shadow = gather_walk(steps)              # the model's impl region
    gathered = real_gather(partitions, n, m, k, size, limit)
    oracle = abstract(gathered, truth, size)

    if oracle == ALIASED:
        return ("DISAGREEMENT: gathered records are not independent objects "
                "(the modeled defect)\n  input=%r\n  shadow=%r\n"
                "  oracle=<aliased gather> gathered=%r" % (inp, shadow, gathered))
    if shadow != oracle:
        return ("DISAGREEMENT\n  input=%r\n  steps=%d\n  shadow=%r\n"
                "  oracle=%r\n  gathered=%r\n  truth=%r"
                % (inp, steps, shadow, oracle, gathered, truth))
    return None


def main():
    from sympy.utilities.iterables import partitions  # REAL patched oracle

    boundary = boundary_inputs()
    # The exact F2P call with a sympy Integer argument, when S imports.
    try:
        from sympy import S
        boundary = boundary + [(S(3), 2, None, False, FULL),
                               (S(3), 2, None, True, FULL),
                               (S(6), None, 2, False, FULL)]
    except Exception:
        pass
    exhaustive = exhaustive_inputs()

    checked = 0
    for inp in boundary:
        err = check_one(partitions, inp)
        if err:
            print("G-CONF FAIL (boundary): " + err)
            return 1
        checked += 1
    n_boundary = checked

    for inp in exhaustive:
        err = check_one(partitions, inp)
        if err:
            print("G-CONF FAIL (exhaustive grid): " + err)
            return 1
        checked += 1
    n_exhaustive = checked - n_boundary

    rng = random.Random(SEED)
    n_fuzz = 0
    while checked < N_TOTAL:
        inp = fuzz_input(rng)
        err = check_one(partitions, inp)
        if err:
            print("G-CONF FAIL (fuzz, seed=%d): " % SEED + err)
            return 1
        checked += 1
        n_fuzz += 1

    print("G-CONF OK: contract-stripped impl region of model.py (gather_walk / "
          "state_at) agrees with the REAL patched "
          "sympy.utilities.iterables.partitions gather on %d inputs "
          "(%d boundary incl. every F2P shape, %d exhaustive grid, %d fuzz, "
          "seed=%d), 0 disagreements."
          % (checked, n_boundary, n_exhaustive, n_fuzz, SEED))
    print(json.dumps({
        "checked": checked,
        "boundary": n_boundary,
        "exhaustive": n_exhaustive,
        "fuzz": n_fuzz,
        "disagreements": 0,
        "seed": SEED,
        "shadow": "direct (contract-stripped impl region of model.py)",
        "oracle": "called: sympy.utilities.iterables.partitions (patched), "
                  "gathered into a list",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
