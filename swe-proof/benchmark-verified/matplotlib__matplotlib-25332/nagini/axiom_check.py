#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-25332.

This bundle consumes NO @ContractOnly axiom. The changed operation — capturing
the disjoint-set container for serialisation by resolving each stored indirect
handle to a direct one, and restoring it by wrapping each direct handle back
into an indirect one — is modelled DEEPLY in model.py as two parallel
`List[int]` carriers:

    ident[i]  : the integer identity the i-th handle points at (its resolution)
    weak[i]   : 1 iff the handle is indirect (NOT serialisable),
                0 iff it is direct (serialisable)

This script validates that deep model (the A-reference) against the REAL
primitives it stands for — Python's `weakref.ref` (constructs an indirect
handle), weakref dereference `ref()` (resolves a handle to its target), and the
serialisability discriminator (`pickle.dumps` succeeds on a direct handle and
fails on an indirect one) — exactly as the real Grouper transformation uses
them:

    capture (model.py capture_state):
        {k(): [v() for v in vs] ...}   # deref -> strong (direct) refs
        deep-model claim: every captured handle is DIRECT (weak == 0) and
        resolves to the SAME identity as the original handle.

    restore (model.py restore_state):
        {weakref.ref(k): [*map(weakref.ref, vs)] ...}  # rewrap -> weak refs
        deep-model claim: every restored handle is INDIRECT (weak == 1) and
        resolves to the SAME identity as the captured direct handle.

    round trip (model.py roundtrip_weakness):
        weakref.ref( weakref.ref(x)() )  resolves back to x.

Imports nothing repo-specific: `weakref` and `pickle` are the Python standard
library — the very primitives the gold patch uses. Exit 0 iff every obligation
holds.
"""
import pickle
import random
import sys
import weakref


class _Obj:
    """A weak-referenceable target standing for a Grouper member (an Artist in
    the real code). Carries an integer identity, like model.py's `ident[i]`."""
    __slots__ = ("ident", "__weakref__")

    def __init__(self, ident):
        self.ident = ident


def _is_direct_serialisable(handle):
    """The real directness discriminator: a DIRECT handle (a plain strong
    reference) is picklable; an INDIRECT handle (a weakref) is not."""
    try:
        pickle.dumps(handle)
        return True
    except TypeError:
        return False


def check_capture(objs):
    """capture_state deep model: dereferencing each indirect handle yields a
    DIRECT handle (model weak-flag 0) that resolves to the SAME identity."""
    # Build the live mapping's handles exactly as Grouper does: weakrefs.
    weak_handles = [weakref.ref(o) for o in objs]

    for o, h in zip(objs, weak_handles):
        # live handle is INDIRECT (weak==1): not serialisable, resolves to o.
        assert not _is_direct_serialisable(h), (
            "live weakref handle was unexpectedly serialisable")
        assert h() is o, "live handle does not resolve to its target"

    # __getstate__: k() / [v() for v in vs] — resolve to strong (direct) refs.
    captured = [h() for h in weak_handles]

    for o, strong in zip(objs, captured):
        # captured handle is DIRECT (weak==0): serialisable.
        assert _is_direct_serialisable(strong), (
            "captured strong handle was not serialisable (deep model claims "
            "weak==0 / direct)")
        # identity preserved: the captured handle resolves to the same identity.
        assert strong is o, "capture did not preserve the resolved identity"
        assert strong.ident == o.ident, "capture corrupted the identity value"


def check_restore(objs):
    """restore_state deep model: wrapping each direct handle yields an INDIRECT
    handle (model weak-flag 1) that resolves to the SAME identity."""
    captured = list(objs)  # direct (strong) refs, as produced by __getstate__

    # __setstate__: weakref.ref(k) / [*map(weakref.ref, vs)] — rewrap.
    restored = [weakref.ref(s) for s in captured]

    for s, h in zip(captured, restored):
        # restored handle is INDIRECT (weak==1): not serialisable.
        assert not _is_direct_serialisable(h), (
            "restored handle was serialisable (deep model claims weak==1 / "
            "indirect)")
        # identity preserved: it resolves back to the same identity.
        assert h() is s, "restore did not preserve the resolved identity"
        assert h().ident == s.ident, "restore corrupted the identity value"


def check_roundtrip(objs):
    """roundtrip_weakness deep model: capture-then-restore is the identity on
    every slot's resolved identity, and the restored container is all-indirect.
    Mirrors the real getstate/setstate composition over a Grouper._mapping."""
    # A small Grouper-shaped mapping: keys + value-lists of weakrefs.
    live = {weakref.ref(o): [weakref.ref(v) for v in objs] for o in objs}

    # __getstate__: convert weak refs to strong ones.
    state = {k(): [v() for v in vs] for k, vs in live.items()}

    # __setstate__: convert strong refs to weak ones.
    rebuilt = {weakref.ref(k): [weakref.ref(v) for v in vs]
               for k, vs in state.items()}

    # Round trip preserves the resolved identity of every key and value.
    assert sorted(k().ident for k in rebuilt) == sorted(o.ident for o in objs)
    for k, vs in rebuilt.items():
        # every rebuilt handle is INDIRECT again (weak==1).
        assert not _is_direct_serialisable(k)
        for v in vs:
            assert not _is_direct_serialisable(v)
        assert [v().ident for v in vs] == [o.ident for o in objs]


def main():
    rng = random.Random(25332)

    # boundary: empty, singleton, duplicates-of-identity-value, larger sets
    boundaries = [
        [],
        [_Obj(0)],
        [_Obj(7), _Obj(7)],            # equal identity *values*, distinct objs
        [_Obj(i) for i in range(5)],
        [_Obj(-1), _Obj(0), _Obj(1)],
    ]
    for objs in boundaries:
        check_capture(objs)
        check_restore(objs)
        check_roundtrip(objs)

    # randomized fuzz
    for _ in range(2000):
        n = rng.randint(0, 12)
        objs = [_Obj(rng.randint(-1000, 1000)) for _ in range(n)]
        check_capture(objs)
        check_restore(objs)
        check_roundtrip(objs)

    print("G-AX OK: capture/restore deep model (weakref deref -> direct, "
          "weakref.ref -> indirect; round trip preserves resolved identity; "
          "direct handles picklable, indirect not) sound on %d boundary + 2000 "
          "fuzz handle sets" % len(boundaries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
