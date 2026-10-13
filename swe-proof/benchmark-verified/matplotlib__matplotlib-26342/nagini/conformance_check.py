#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26342 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model IS Python; the impl is two plain
attribute assignments, so the shadow is the impl run directly. The modeled
collection object is realized as the minimal two-field class the model
declares. There are no @Pure helpers with executable content and no
@ContractOnly callees in this bundle (axioms region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md — the
base ``matplotlib.collections.Collection.set_paths``. The gate applies the
gold patch to /testbed before this script runs and sets PYTHONPATH=/testbed,
so the patched module is what imports here. This script does NOT apply any
patch itself.

Type bridge (mapping.md section 2): the model carries the supplied geometry
sequence as ``List[int]`` of opaque per-item identity tokens; the repo side
carries a ``list`` of ``matplotlib.path.Path`` objects. The bijection maps
each Path to its CPython identity (``id``): per-index element identity, list
length, stored-reference identity (``is``), and the boolean out-of-date flag
are the observables compared. The shadow runs on a token list of the same
length as the oracle's Path list; both sides' observation tuples must match:
  (stored object IS the supplied object, flag value,
   supplied list length unchanged, per-index elements unchanged).

Input domain: the model's Requires demands only field access on the receiver
and (fractionally) on the supplied sequence — every (collection state,
sequence) pair is Requires-satisfying. Fuzz varies: sequence length 0..8,
receiver pre-state (freshly constructed / flag forced low / a previous
sequence already installed / repeated installs on one receiver), and the
receiver class among those that genuinely dispatch to the modeled BASE
method (bare Collection; PathCollection, which post-patch inherits the base
method — asserted; plus one ContourSet observation, the failing-test
subject). Classes that override the method with data-rebuilding semantics
are outside the modeled scope (mapping.md section 3.1) and are not fed here.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz cases.
Pinned fuzz seed: 2634201.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

SEED = 2634201
N_FUZZ = 100_000


# --- the modeled object, as declared in model.py (contracts stripped) ---------

class GeometryCollection:
    def __init__(self):
        self.items = []
        self.out_of_date = False


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def install_geometry(self, new_items):
    self.items = new_items
    self.out_of_date = True


# --- observation: the same tuple of observables on either side ----------------

def observe_shadow(coll, seq):
    """Run the shadow and report (identity, flag, len-preserved, elems-preserved)."""
    before_len = len(seq)
    before_ids = [id(x) for x in seq]
    install_geometry(coll, seq)
    return (coll.items is seq,
            coll.out_of_date is True,
            len(seq) == before_len,
            [id(x) for x in seq] == before_ids)


def observe_real(coll, paths):
    """Run the real patched setter and report the same observable tuple."""
    before_len = len(paths)
    before_ids = [id(p) for p in paths]
    coll.set_paths(paths)
    return (coll.get_paths() is paths,
            coll.stale is True,
            len(paths) == before_len,
            [id(p) for p in paths] == before_ids)


def main():
    import matplotlib
    matplotlib.use("Agg")  # headless
    import numpy as np
    from matplotlib.path import Path
    from matplotlib.collections import Collection, PathCollection

    # Scope guard: the oracle is the BASE method. PathCollection must dispatch
    # to it post-patch (its identical subclass override is gone), otherwise the
    # environment is not the patched state this check targets.
    if not (PathCollection.set_paths is Collection.set_paths):
        print("G-CONF ERROR: PathCollection does not dispatch to the base "
              "method; the mounted repo does not look patched.")
        return 1

    # A reusable pool of real Path objects: the operation under test treats
    # items as opaque (stores the list reference, never inspects elements),
    # so element identity, not element freshness, is what matters.
    pool = [Path(np.array([[float(i), 0.0], [0.0, float(i) + 1.0]]))
            for i in range(16)]

    rng = random.Random(SEED)
    checked = 0
    disagreements = 0

    def check_case(label, real_coll, n, pre_flag_low=False, pre_install=False):
        nonlocal checked, disagreements
        # shadow side: token list of length n on a receiver in matching pre-state
        sh = GeometryCollection()
        if pre_install:
            install_geometry(sh, [rng.randrange(100) for _ in range(rng.randrange(4))])
        if pre_flag_low:
            sh.out_of_date = False
        tokens = [rng.randrange(1000) for _ in range(n)]
        got_shadow = observe_shadow(sh, tokens)

        # real side: Path list of the same length on the supplied receiver
        if pre_install:
            real_coll.set_paths([pool[rng.randrange(len(pool))]
                                 for _ in range(rng.randrange(4))])
        if pre_flag_low:
            real_coll.stale = False
        paths = [pool[rng.randrange(len(pool))] for _ in range(n)]
        got_real = observe_real(real_coll, paths)

        checked += 1
        if got_shadow != got_real:
            disagreements += 1
            print("DISAGREEMENT [%s]\n  n=%d pre_flag_low=%r pre_install=%r\n"
                  "  shadow tokens=%r -> %r\n  real paths(ids)=%r -> %r"
                  % (label, n, pre_flag_low, pre_install,
                     tokens, got_shadow, [id(p) for p in paths], got_real))
            return False
        return True

    # --- boundary cases -------------------------------------------------------
    boundaries = [
        ("empty seq / fresh Collection", Collection(), 0, False, False),
        ("singleton / fresh Collection", Collection(), 1, False, False),
        ("empty seq / flag low", Collection(), 0, True, False),
        ("re-install over previous seq", Collection(), 3, False, True),
        ("re-install + flag low", Collection(), 2, True, True),
        ("empty seq / PathCollection", PathCollection([]), 0, False, False),
        ("PathCollection with prior contents", PathCollection(pool[:3]), 4, True, False),
    ]
    for label, coll, n, low, pre in boundaries:
        if not check_case(label, coll, n, low, pre):
            return 1

    # One observation on the failing-test subject class, which inherits the
    # base method (asserted) — construction is heavy, so a single case.
    import matplotlib.pyplot as plt
    fig = plt.figure()
    cs = fig.subplots().contour([[0, 1], [1, 2]])
    assert type(cs).set_paths is Collection.set_paths
    if not check_case("ContourSet (inherits base method)", cs, 5, False, False):
        return 1
    plt.close(fig)

    # Repeated installs on ONE long-lived receiver: each call must still
    # satisfy the observables (stored-reference identity swaps to the new
    # object each time).
    long_lived_real = Collection()
    long_lived_shadow = GeometryCollection()
    for k in range(200):
        n = rng.randrange(0, 9)
        tokens = [rng.randrange(1000) for _ in range(n)]
        paths = [pool[rng.randrange(len(pool))] for _ in range(n)]
        if k % 3 == 0:
            long_lived_shadow.out_of_date = False
            long_lived_real.stale = False
        got_shadow = observe_shadow(long_lived_shadow, tokens)
        got_real = observe_real(long_lived_real, paths)
        checked += 1
        if got_shadow != got_real:
            disagreements += 1
            print("DISAGREEMENT [long-lived receiver, install #%d]\n"
                  "  shadow -> %r\n  real -> %r" % (k, got_shadow, got_real))
            return 1

    # --- fuzz: 100000 Requires-satisfying cases -------------------------------
    for i in range(N_FUZZ):
        n = rng.randrange(0, 9)
        pre_flag_low = rng.random() < 0.5
        pre_install = rng.random() < 0.3
        # mostly bare Collection (cheap); a slice of PathCollection to keep the
        # inherited-dispatch site exercised throughout
        if i % 20 == 0:
            coll = PathCollection([])
        else:
            coll = Collection()
        if not check_case("fuzz#%d" % i, coll, n, pre_flag_low, pre_install):
            return 1

    print("G-CONF OK: shadow impl == real patched base setter on %d inputs "
          "(%d boundary + 1 failing-test subject + 200 long-lived-receiver + "
          "%d fuzz, seed %d); observables: stored-reference identity, "
          "out-of-date flag, supplied-sequence preservation."
          % (checked, len(boundaries), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": disagreements,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
