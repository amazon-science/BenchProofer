# refinement.md — matplotlib__matplotlib-23476

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`finalizeSnapshot` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no A legs** (no axioms,
no A-references): the step calls no outside routine. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The serialization site — `Figure.__getstate__` (`lib/matplotlib/figure.py:3015`)

Gold hunk (added between the cached-renderer reset and the version stamp):
```
+        # discard any changes to the dpi due to pixel ratio changes
+        state["_dpi"] = state.get('_original_dpi', state['_dpi'])
```

| # | Solution.lean impl op (`finalizeSnapshot`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `snap : SurfaceSnapshot` (fields `resolution`, `baseline`, `payload`) | the `state` dict in scope (already assembled by `super().__getstate__()` + the prior hook lines) | R | `state` dict ↔ `SurfaceSnapshot` (mapping.md §2): `state['_dpi']` ↔ `resolution`, `state.get('_original_dpi', …)` ↔ `baseline : Option Float`, the rest ↔ `payload`. G-CONF bridges via that dict view. |
| A2 | `snap.baseline.getD snap.resolution` | `state.get('_original_dpi', state['_dpi'])` | I | `dict.get(k, d)` is exactly `Option.getD`: the recorded reference value when the key is present, else the supplied default `state['_dpi']`. Concrete op, transliterated verbatim by G-CONF. |
| A3 | `return { snap with resolution := … }` (one field updated) | `state["_dpi"] = …` (one key reassigned) | I | record field update ↔ dict-key assignment; both write only the resolution slot and leave the rest of the carrier intact. G-CONF reads back `_dpi` and every other entry. |
| A4 | frame: `out.baseline = snap.baseline`, `out.payload = snap.payload` | the added line writes only `state['_dpi']`; `_original_dpi` and all other entries are untouched | R + I | directive-5 frame: `snap` is read-only (not `mut`); `{snap with …}` rebuilds every other field identically. G-CONF confirms no other `state` entry changes. |

Discriminating content of the change — when a reference value was captured
(`baseline = some v`), the persisted resolution becomes `v`, **not** the working
value `snap.resolution` — lives in `out.resolution = snap.baseline.getD
snap.resolution` (spec) ⇔ the `state.get('_original_dpi', …)` selection (real).
The pre-patch hook persisted the working `_dpi` unchanged;
`Solution_prepatch.lean` reproduces that (`return snap`) and **fails** the
`out.resolution = snap.baseline.getD snap.resolution` clause (G-DIFF) exactly
when `baseline = some _` — the case the F2P test
`test_unpickle_with_device_pixel_ratio` exercises (it raises the device pixel
ratio so `_dpi = 42*7` while `_original_dpi = 42`, then asserts the reloaded dpi
is `42`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — choosing
which dpi value the serialized state carries — is a concrete dictionary-lookup
selection modeled **directly** as `Option.getD` (steps A2/A3, **I**), not hidden
behind any axiom. There is no consumed axiom and no deep-model reference: the
step performs no call to a repository or library routine. mapping.md §3 records
this absence explicitly.

## C. verify(Solution) ⇒ resolved

`finalizeSnapshot` verifies only if its output resolution equals `snap.baseline.getD
snap.resolution` (A2) — the reference value when present, the working value
otherwise — AND the reference value and the rest of the snapshot are preserved
(A4 frame). By R (`state` dict ↔ `SurfaceSnapshot`, `dict.get` ↔ `Option.getD`,
key-assignment ↔ field-update) the verified step equals the gold line
`state["_dpi"] = state.get('_original_dpi', state['_dpi'])` on every `state` the
F2P/P2P tests produce; by G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour on ≥10⁵ fuzzed inputs plus a live high-pixel-ratio
`Figure` round-trip. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point here is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point because the bundle has no axioms.
