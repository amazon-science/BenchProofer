# refinement.md — django__django-17029

The operation-by-operation correspondence between `Solution.lean`'s `do` block
(the `clearAllCaches` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement — same operation, refined carrier type),
**A-consumed** (the proof uses an axiom's `ensures`), **A-reference** (a deep
model / representation is validated == the real callee by `axiom_check.py` /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The cache-reset site — `Apps.clear_cache()` (`django/apps/registry.py:370`)

Gold hunk (one added line):
```
 This is mostly used in tests.
 """
+self.get_swappable_settings_name.cache_clear()
 # Call expire cache on each model. ...
 self.get_models.cache_clear()
```

| # | Solution.lean impl op (`clearAllCaches`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `(mut modelsOccupancy) (mut swappableOccupancy)` | `self` (an `Apps` instance) | R | `Apps` ↔ the two touched cache occupancies; only the observable state the reset touches/promises is modeled (mapping.md §1, §2). |
| A2 | `swappableOccupancy := 0` | `self.get_swappable_settings_name.cache_clear()` (the **added** line) | R + A-reference | `cache_clear()` on `get_swappable_settings_name`'s `functools._lru_cache_wrapper` empties its cache, after which `cache_info().currsize == 0`. The occupancy `Nat` is the refinement of `currsize`, and assigning `0` is the refinement of `cache_clear()`'s documented effect on it (mapping.md §2). The fact `cache_clear() ⇒ currsize == 0` is about the UNCHANGED stdlib `functools.cache` callee, NOT consumed as an axiom; it is validated == the real callee out-of-band by `axiom_check.py` (G-AX), hence **A-reference**. |
| A3 | `modelsOccupancy := 0` | `self.get_models.cache_clear()` (pre-existing line, unchanged) | R + A-reference | identical representation refinement to A2 for the all-models lookup cache. Present pre- and post-patch alike; same `functools.cache` A-reference fact. |

The model-expiry loop (`registry.py:379-384`) is omitted (mapping.md §2): it is
unchanged by the patch and performs no `cache_clear()` on either wrapper, so it
neither establishes nor disturbs the two zero-occupancy postconditions.

The discriminating content of the change — that the reset clears **every**
memoizing method's cache, specifically also the swappable-settings-name one —
lives in the postcondition `swappableOccupancy = 0`. The pre-patch code clears
only `get_models` (A3) and never touches `get_swappable_settings_name` (A2 is
absent); `Solution_prepatch.lean` reproduces that (it drops the
`swappableOccupancy := 0` write) and **fails** the postcondition
`swappableOccupancy = 0` — exactly the spec sensing the change (G-DIFF, unsolved
goal `swappableOccupancyOld = 0`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R (with an A-reference soundness anchor on the `functools`
fact). The one operation that genuinely *changed* — adding the clearing of the
swappable-settings-name cache — is modeled **directly** as the state write
`swappableOccupancy := 0` (the representation refinement of
`get_swappable_settings_name.cache_clear()`), not hidden behind an axiom about
the function under change. There is **no consumed axiom**: the proof's
postconditions are concrete equalities on the registry's own state. The only
external fact relied on (`cache_clear() ⇒ currsize == 0` for a `functools.cache`
wrapper) is an **A-reference** that G-AX validates against the real `functools`
callee (`axiom_check.py`), never a consumed axiom.

## C. verify(model) ⇒ resolved

`clearAllCaches` verifies only if, on return, BOTH `modelsOccupancy` and
`swappableOccupancy` are `0` (the two postconditions). By R (`Apps` ↔ the two
occupancies; `cache_info().currsize` ↔ the `Nat`; `method.cache_clear()` ↔
`field := 0`, validated by G-AX as an A-reference on the unchanged
`functools.cache` callee), the verified reset equals
`self.get_swappable_settings_name.cache_clear(); self.get_models.cache_clear()`
on the registry's two `@functools.cache` methods. That is exactly what the F2P
test `test_clear_cache` observes — after `apps.clear_cache()` it asserts
`apps.get_swappable_settings_name.cache_info().currsize == 0` AND
`apps.get_models.cache_info().currsize == 0`. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement, and the
gold patch resolves (G-RESOLVE). The trust points reduce to: refinement fidelity
(this document, G-EQ) and the single `functools.cache` fact (G-AX, §A2/A3).
