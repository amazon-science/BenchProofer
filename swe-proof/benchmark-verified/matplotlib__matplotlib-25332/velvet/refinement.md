# refinement.md — matplotlib__matplotlib-25332

Operation-by-operation correspondence between `Solution.lean`'s two impl regions
(`snapshot`, `rebuild`, with the deep models `strongifyMap` / `weakenMap`) and
`patch.diff` (the gold patch adding `Grouper.__getstate__` / `__setstate__`).
Each step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated == an
unchanged real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the maps below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The snapshot site — `Grouper.__getstate__` (`lib/matplotlib/cbook.py`, added by the patch)

Gold hunk:
```
+ def __getstate__(self):
+     return {
+         **vars(self),
+         # Convert weak refs to strong ones.
+         "_mapping": {k(): [v() for v in vs] for k, vs in self._mapping.items()},
+     }
```

| # | Solution.lean impl op (`snapshot`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `mapping : List (Ref × List Ref)` | `self._mapping` (an ordered `dict`) | R | `dict` ↔ `List (key × group)` via `list(d.items())`; insertion order preserved both sides (mapping.md §2). A `weakref.ref` ↔ `Ref{ target := id(referent), weak := true }`. |
| A2 | result is `strongifyMap mapping`: each row's key and every group member made strong (`weak := false`) keeping `target`, computed by the backward `while` fold | `{k(): [v() for v in vs] for k, vs in self._mapping.items()}` | I | the changed op is modeled **deeply**: `strongify`/`strongifyEntry`/`strongifyMap` (pure region) and the verified loop ARE the comprehension. `k()` / `v()` (dereference the weak ref to the strong object) ↔ `strongify` (flip `weak` false, keep `target`). The fold ops are **I** (concrete, transliterated by G-CONF). No consumed axiom. |
| A3 | `mapping` is a read-only param (not `mut`); only `result` is built and returned | `__getstate__` reads `self._mapping`, returns a **new** dict; `self` is not mutated (directive 5) | I + R | the snapshot does not alter the live table in place. The `**vars(self)` carry-over of other instance attributes is content the F2P does not observe through the `_mapping` channel (mapping.md §2); modeled as identity, omitted. |

Discriminating content of the change — a live weak reference is replaced by a
**strong** reference to the same object — lives in
`strongify r = { r with weak := false }` (model) ⇔ `k()`/`v()` dereference
(real). `Solution_prepatch.lean` models the pre-fix behaviour (no snapshot
step: the live weak table handed out verbatim, modeled as identity over rows)
and **fails** `out = strongifyMap mapping` at the loop body (G-DIFF), because a
weak reference (`weak = true`) ≠ its strongified form (`weak = false`).

## B. The rebuild site — `Grouper.__setstate__` (`lib/matplotlib/cbook.py`, added by the patch)

Gold hunk:
```
+ def __setstate__(self, state):
+     vars(self).update(state)
+     # Convert strong refs to weak ones.
+     self._mapping = {weakref.ref(k): [*map(weakref.ref, vs)]
+                      for k, vs in self._mapping.items()}
```

| # | Solution.lean impl op (`rebuild`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `state : List (Ref × List Ref)` | the stored `state` dict's `_mapping` (strong refs) | R | same `dict` ↔ `List` bijection; a strong reference ↔ `Ref{ weak := false }`. |
| B2 | result is `weakenMap state`: each row's key and every group member made weak (`weak := true`) keeping `target` | `{weakref.ref(k): [*map(weakref.ref, vs)] for k, vs in self._mapping.items()}` | I | modeled **deeply**: `weaken`/`weakenEntry`/`weakenMap` and the verified loop ARE the comprehension. `weakref.ref(k)` / `map(weakref.ref, vs)` (make a live weak reference to the strong object) ↔ `weaken` (flip `weak` true, keep `target`). Fold ops are **I**. No consumed axiom. |
| B3 | postcondition `∀ r, weaken (strongify r) = weaken r` | the loss-free round-trip the patch guarantees: read-back after snapshot restores a live weak reference to the same object | I | structural fact about the two deep models (`weaken_strongify` lemma); ties the snapshot (A) and rebuild (B) legs so the spec pins that the pair is the identity on what a live table observes (which object each reference targets), grounding the postcondition in the input (directive 8) rather than an oracle. |

`Solution_prepatch_2.lean` models the pre-fix behaviour of this site (no
read-back conversion: the stored strong table adopted verbatim, modeled as
identity over rows) and **fails** `out = weakenMap state` at the loop body
(G-DIFF), because a strong reference (`weak = false`) ≠ its weakened form
(`weak = true`).

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The two operations that genuinely *changed* — the weak↔
strong per-reference conversions — are modeled **deeply** (the spelled-out folds
`strongifyMap` / `weakenMap`), not hidden behind an axiom about the function
under change. There is **no consumed axiom and no A-reference**: neither changed
function calls an *unchanged* foreign callee whose contract the proof assumes
(the `weakref.ref(·)` / `·()` primitives ARE the modeled change, not an
unchanged callee — mapping.md §3). Hence no `axiom_check.py`; G-AX is not
applicable (mapping.md §3: at `base_commit` the methods do not yet exist, so
there is no unchanged real callee to validate). Soundness of the deep models is
established against the *patched* repo by G-CONF (§D).

## D. verify(Solution) ⇒ resolved

`snapshot` verifies only if its output equals `strongifyMap mapping` (A2: every
reference made strong, keeping its target object); `rebuild` verifies only if
its output equals `weakenMap state` (B2: every reference made weak) and the
loss-free round-trip holds (B3). By R (the `dict ↔ List (Ref × List Ref)`
bijection, mapping.md §2) the verified `snapshot` equals the real
`__getstate__`'s `_mapping` comprehension and the verified `rebuild` equals the
real `__setstate__`'s, on every reference table. G-CONF mechanically confirms
this over ≥10⁵ fuzzed tables against the patched repo (zero disagreements). The
F2P (`test_complete[png]` after `align_ylabels()`) pickles a figure whose
`_align_label_groups` hold `Grouper`s of weak references: with the snapshot
converting them to strong (picklable) refs and the rebuild restoring weak refs
on load, `pickle.dumps`/`loads` round-trips — exactly what the two verified
methods guarantee. Therefore a model satisfying this spec, refined by the maps
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point (no axioms).
