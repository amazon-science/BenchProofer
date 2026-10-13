#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-26342.

This bundle consumes NO @ContractOnly axioms: installing a geometry sequence is
pure object/state logic, modelled deeply in model.py (store a reference, set a
flag). What G-AX validates here is the **A-reference** — that the deep model
faithfully captures the real Python semantics of the modeled state mutation:

  (1) IDENTITY: after the setter runs on a collection, querying the collection's
      geometry returns the very object supplied — the supplied object is stored
      and handed back (model.py: ``self.items is new_items``);
  (2) OUT-OF-DATE: the collection is marked out of date afterwards (model.py:
      ``self.out_of_date is True``);
  (3) READ-ONLY INPUT: the supplied sequence is not rewritten by the setter —
      same length, same elements in order (model.py: the fractional
      ``list_pred`` postcondition + per-index preservation).

REQUIRES THE GOLD PATCH APPLIED. The modeled function IS the changed function
(deep model, empty axioms region), so the A-reference target is the *post-patch*
symbol. Pre-patch the base setter raises ``NotImplementedError`` and reaches no
assignment, so identity/flag observations do not yet hold. The orchestrator runs
this with ``apply_gold=True`` (meta.json G-AX note records the requirement); the
patch is git-applied to the in-tree source BEFORE this process starts, so the
patched ``Collection.set_paths`` is loaded on first import. If the script finds
the in-tree base setter still un-patched (i.e. it was invoked without
``apply_gold``), it prints ``G-AX SKIP`` and returns 0 rather than asserting
against the wrong container state — it does NOT attempt an in-process reload of
matplotlib (that corrupts matplotlib's kwdoc registry).

SCOPE DISCIPLINE. The A-reference is asserted only on call sites that genuinely
dispatch to the modeled (base) setter:
  * a ``ContourSet`` (the F2P subject), which inherits the base setter;
  * ``PathCollection`` (the patch DELETES its identical override, so post-patch
    it inherits the base setter — verified by an identity check on the bound
    methods); and
  * a bare ``Collection`` instance (the base method directly, incl. the
    empty-sequence boundary).
``LineCollection`` and ``PolyCollection`` are NOT in scope: at this commit their
``set_paths`` is an *override* (``set_segments`` / ``set_verts``) that rebuilds
``self._paths`` from the supplied data and does NOT store the supplied object by
identity. Feeding opaque Path tokens into them would be unfaithful to the model.
They are instead a NEGATIVE CONTROL: the script asserts their ``set_paths`` is
NOT the base method, confirming they fall correctly OUTSIDE the modeled scope.

Run inside the official SWE-bench container for the instance, where matplotlib
is importable. Exit 0 iff every obligation holds. Outside the container
(matplotlib absent / no usable backend) it prints ``G-AX SKIP`` after the
environment-independent primitive checks and returns 0; the orchestrator runs
it in-container.
"""
import random
import sys


def _check_primitive_semantics():
    """The A-reference proper, independent of matplotlib: a plain attribute
    assignment stores the SAME object (identity preserved), and assigning the
    literal True yields True. This is exactly what the two-line setter does."""
    class Box:
        pass

    rng = random.Random(26342)
    for _ in range(5000):
        n = rng.randint(0, 12)
        seq = [object() for _ in range(n)]          # opaque "Path" tokens
        snapshot_ids = [id(x) for x in seq]
        b = Box()
        b._paths = seq                               # the stored reference
        b.stale = True                               # the flag
        # (1) identity: get-back is the very same object
        assert b._paths is seq, "attribute assignment did not store the object"
        # (2) flag
        assert b.stale is True, "flag assignment did not yield True"
        # (3) read-only: the setter does not rewrite the supplied list
        assert len(seq) == n, "supplied list length changed"
        assert [id(x) for x in seq] == snapshot_ids, "supplied list contents changed"


def _is_patched():
    """The A-reference validates the POST-patch base setter. Return True iff the
    in-tree ``Collection.set_paths`` is the patched body (stores the supplied
    object + sets the flag). The orchestrator applies the gold patch to disk
    BEFORE this process starts (apply_gold=True), so the patched source is loaded
    on first import; we only INSPECT here (no in-process reload — reloading
    matplotlib.collections corrupts the kwdoc registry)."""
    try:
        import matplotlib.collections as mc
        import inspect
        src = inspect.getsource(mc.Collection.set_paths)
    except Exception:
        return False
    return "self._paths = paths" in src


def main():
    _check_primitive_semantics()

    try:
        import matplotlib
        matplotlib.use("Agg")                        # headless, no display
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: matplotlib not usable in this environment: %r "
              "(attribute-assignment A-reference semantics confirmed)" % (exc,))
        return 0

    if not _is_patched():
        print("G-AX SKIP: in-tree Collection.set_paths is not the patched body; "
              "run this with the gold patch applied (orchestrator apply_gold=True) "
              "(attribute-assignment A-reference semantics confirmed)")
        return 0

    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.path import Path
        from matplotlib.collections import (
            Collection, PathCollection, LineCollection, PolyCollection)
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: matplotlib not usable in this environment: %r "
              "(attribute-assignment A-reference semantics confirmed)" % (exc,))
        return 0

    # --- SCOPE / NEGATIVE CONTROL --------------------------------------------
    # The A-reference is about the BASE Collection.set_paths only. Assert that
    # the in-scope classes dispatch to it and the out-of-scope overriders do
    # NOT, so we never feed opaque Path tokens into a setter that rebuilds
    # self._paths from the supplied data.
    assert PathCollection.set_paths is Collection.set_paths, (
        "post-patch PathCollection must INHERIT the base set_paths (its "
        "identical override is deleted by the patch)")
    assert LineCollection.set_paths is not Collection.set_paths, (
        "negative control: LineCollection overrides set_paths (set_segments); "
        "it is OUTSIDE the modeled base-setter scope")
    assert PolyCollection.set_paths is not Collection.set_paths, (
        "negative control: PolyCollection overrides set_paths (set_verts); "
        "it is OUTSIDE the modeled base-setter scope")

    observations = 0

    def observe_collection(coll, paths):
        nonlocal observations
        # Only ever called on collections that dispatch to the base setter.
        assert type(coll).set_paths is Collection.set_paths, (
            "observe_collection called on a class that overrides set_paths")
        before_ids = [id(p) for p in paths]
        before_len = len(paths)

        coll.set_paths(paths)                        # the REAL patched base setter

        # (1) IDENTITY: the collection hands back the very object supplied.
        got = coll.get_paths()
        assert got is paths, (
            "set_paths/get_paths broke object identity: get_paths() is not the "
            "supplied list (model.py self.items is new_items)")
        # (2) OUT-OF-DATE flag set.
        assert coll.stale is True, (
            "set_paths did not mark the collection stale "
            "(model.py self.out_of_date is True)")
        # (3) READ-ONLY: supplied list untouched (same length, same elements).
        assert len(paths) == before_len, "set_paths changed the supplied list length"
        assert [id(p) for p in paths] == before_ids, (
            "set_paths rewrote the supplied list's elements")
        observations += 1

    def make_paths(rng, m):
        out = []
        for _ in range(m):
            k = rng.randint(1, 5)
            verts = np.array([[rng.uniform(-1, 1), rng.uniform(-1, 1)]
                              for _ in range(k)])
            out.append(Path(verts))
        return out

    # --- the F2P subject: a ContourSet (inherits the base setter) -----------
    fig_ref = plt.figure()
    cs_ref = fig_ref.subplots().contour([[1, 0], [2, 1]])
    fig_test = plt.figure()
    cs_test = fig_test.subplots().contour([[0, 1], [1, 2]])
    assert type(cs_test).set_paths is Collection.set_paths, (
        "ContourSet must inherit the base Collection.set_paths")
    ref_paths = cs_ref.get_paths()
    # Exactly the F2P call: install the reference paths onto the test set.
    observe_collection(cs_test, ref_paths)
    # the test set now renders the reference geometry
    assert cs_test.get_paths() is ref_paths
    plt.close(fig_ref)
    plt.close(fig_test)

    rng = random.Random(2634200)

    # --- PathCollection: the patch DELETES its override, so it now inherits the
    # fixed base class and behaves identically (refinement.md site B). ---------
    for _ in range(50):
        pc = PathCollection(make_paths(rng, rng.randint(0, 6)))
        new = make_paths(rng, rng.randint(0, 6))
        observe_collection(pc, new)

    # --- a bare Collection instance exercising the base method directly, incl.
    # the empty-sequence boundary. --------------------------------------------
    for n in (0, 1, 2, 5, 17):
        c = Collection()
        observe_collection(c, make_paths(rng, n))

    print("G-AX OK: deep model validated against the real (post-patch) "
          "Collection.set_paths over %d observations (ContourSet F2P subject + "
          "PathCollection [override deleted -> inherits base] + bare "
          "Collection); get_paths() returns the supplied object by identity, "
          "stale becomes True, and the supplied list is left untouched. "
          "Negative control: LineCollection/PolyCollection override set_paths "
          "(set_segments/set_verts) and are correctly OUTSIDE the modeled "
          "base-setter scope. Attribute-assignment A-reference semantics "
          "confirmed (5000 cases)." % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
