# refinement.md — matplotlib__matplotlib-25332

The operation-by-operation correspondence between `model.py`'s implementation
(`capture_state`, `restore_state`, `roundtrip_weakness`) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed**, the proof uses the axiom's `Ensures`; **A-reference**,
a deep model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The capture site — `__getstate__` (`lib/matplotlib/cbook.py`, ADDED)

Gold hunk:
```python
def __getstate__(self):
    return {
        **vars(self),
        # Convert weak refs to strong ones.
        "_mapping": {k(): [v() for v in vs] for k, vs in self._mapping.items()},
    }
```

| # | model.py impl op (`capture_state`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `ident: List[int]`, `weak: List[int]` (the handles of `_mapping`, flattened) | the dict `self._mapping` (weakref keys + weakref value-lists) | R | each `weakref.ref`/strong handle ↔ a slot `(ident[i], weak[i])`; the dict's keys and value-list elements undergo the same per-handle transform, so they flatten to one list (mapping.md §1, §2). |
| A2 | the loop produces `out` with `out[k] == 0` for every slot; `ident` left untouched (read at 1/2 perm) | `{k(): [v() for v in vs] ...}` — deref every weakref to its strong referent | A-reference | the changed string/handle operation is modeled **deeply**: "produce a direct handle (flag 0) for every slot, preserving its resolved identity" IS the dereference `k()`/`v()`. There is no consumed axiom. The deep model is validated == the real primitive out-of-band: G-AX (`check_capture`) runs the real weakref deref + `pickle.dumps` and asserts the captured handle is picklable (direct, flag 0) and `h() is o` (identity preserved). |
| A3 | `out` returned (a `List[int]` of directness flags), `ident` unchanged | the returned dict (`**vars(self)` merged with the strong-ref `_mapping`) | R | the captured value's tested-relevant projection is "no weakref survives" (= all flags 0); `**vars(self)` carries the other attributes unchanged and the strong refs preserve identity (`ident` immutable). |

The discriminating content of the change — the captured state must contain **no
weakref** (every handle direct) — lives in `Ensures(... Result()[k] == 0)`.
Pre-patch there is no `__getstate__`, so the default pickle state is
`vars(self)` with `_mapping`'s weakrefs **unchanged** (every handle still
indirect); `model_prepatch.py` reproduces that (`capture_state` returns the
live directness flags `weak[i]`, which are 1) and **fails** the postcondition
`Result()[k] == 0` — exactly the spec sensing the bug (G-DIFF). That surviving
weakref is what raises `TypeError: cannot pickle 'weakref.ReferenceType'`.

## B. The restore site — `__setstate__` (`lib/matplotlib/cbook.py`, ADDED)

Gold hunk:
```python
def __setstate__(self, state):
    vars(self).update(state)
    # Convert strong refs to weak ones.
    self._mapping = {weakref.ref(k): [*map(weakref.ref, vs)]
                     for k, vs in self._mapping.items()}
```

| # | model.py impl op (`restore_state`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `ident`, `state_weak` with `Requires(state_weak[k] == 0)` (the captured state is all-direct) | `state` (the captured dict of strong refs) merged via `vars(self).update(state)` | R | the captured state being restored is the output of `__getstate__` — all direct handles (flags 0); the precondition mirrors that. |
| B2 | the loop produces `out` with `out[k] == 1` for every slot; `ident` untouched | `{weakref.ref(k): [*map(weakref.ref, vs)] ...}` — rewrap every strong ref into a weakref | A-reference | "produce an indirect handle (flag 1) for every slot, preserving its resolved identity" IS `weakref.ref(k)`/`map(weakref.ref, vs)`. Deep-modeled, validated by G-AX (`check_restore`): the restored handle is NOT picklable (indirect, flag 1) and `h() is s` (identity preserved). |
| B3 | `out` returned (all flags 1), `ident` unchanged | the rebuilt weakref `_mapping` assigned to `self._mapping` | R | the restored container's tested-relevant projection is "every handle is a weakref again" (all flags 1), restoring the live form. |

## C. The round trip — `roundtrip_weakness` ↔ getstate∘setstate

| # | model.py impl op (`roundtrip_weakness`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `captured = capture_state(ident, weak)` | `__getstate__` | I + A-reference | the same capture (A2); invoked under spec (the callee's contract), not an axiom. |
| C2 | `restored = restore_state(ident, captured)` | `__setstate__` | I + A-reference | the same restore (B2); `capture_state`'s postcondition (`captured[k]==0`) discharges `restore_state`'s precondition. |
| C3 | `return restored` (all flags 1; `ident` preserved) | the unpickled Grouper, equivalent to the original | R | composition: the round trip yields an all-indirect container resolving to the same identities — the unpickle of the pickle. The F2P test (`test_complete`) pickles a figure whose `_align_label_groups` Groupers were populated by `align_ylabels()` and unpickles it; this is exactly C1∘C2 over those Groupers. |

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operations that genuinely
*changed* — resolving each indirect handle to a direct one (capture) and
wrapping each direct handle back into an indirect one (restore) — are modeled
**deeply** (the spelled-out directness/identity transform in the two verified
loops), NOT hidden behind an axiom about the function under change. There is no
consumed `@ContractOnly` axiom; the real primitives (`weakref.ref`, weakref
dereference, the pickle directness discriminator) appear only as **A-reference**
that G-AX validates the deep model against.

## E. verify(model) ⇒ resolved

`capture_state` verifies only if its output is all-direct (A2: every flag 0)
over an unchanged identity carrier; `restore_state` only if all-indirect (B2)
over the same; `roundtrip_weakness` only if their composition is all-indirect
and identity-preserving (C). By R (handle ↔ (ident, weak) slot; dict ↔ flat
list; `**vars(self)` identity), the verified capture equals the gold
`__getstate__` (a state with no surviving weakref → picklable) and the verified
restore equals the gold `__setstate__` (weakrefs rebuilt) on the tested
Groupers. By G-AX the deep models equal the real weakref/pickle primitives
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and audited primitives — and the gold
patch resolves (G-RESOLVE: the figure pickle round trip in `test_complete`
succeeds where pre-patch it raised `TypeError`). The trust points are exactly
the two of PLAN §1.1: deep-model/primitive soundness (G-AX) and refinement
fidelity (this document, G-EQ).
