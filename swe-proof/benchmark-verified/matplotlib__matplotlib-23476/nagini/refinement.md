# refinement.md — matplotlib__matplotlib-23476

The operation-by-operation correspondence between `model.py`'s implementation
(the `normalize_state_dpi` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed** / **A-reference**), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **byte-for-byte** — the `instance.json` `patch`
field written verbatim, including the blank-context-line trailing whitespace (it
applies at `base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The DPI-reconciliation site — `Figure.__getstate__` (`lib/matplotlib/figure.py:3015`)

Gold hunk (added between the renderer-clearing and version-stamping lines):
```
+ # discard any changes to the dpi due to pixel ratio changes
+ state["_dpi"] = state.get('_original_dpi', state['_dpi'])
```

| # | model.py impl op (`normalize_state_dpi`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `state: Dict[int, int]` | the local `state` mapping (`super().__getstate__()` → `self.__dict__.copy()`) | R | `dict` (`str`→value) ↔ `Dict[int, int]` (entry-name token → value token); only the two touched keys are observed (mapping.md §2). |
| A2 | `key_dpi() in state` membership test guarding the selection | the `.get('_original_dpi', ...)` lookup-with-default — equivalently, the membership of `'_original_dpi'` decides whether the default is used | R + I | `if key_original_dpi() in state` ↔ "`'_original_dpi'` is a key of `state`"; the model spells out the `.get(k, default)` semantics deeply (whence the `else` self-assign), so this is an identical control decision under the key-token refinement. |
| A3 | `state[key_dpi()] = state[key_original_dpi()]` (present branch) | `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` when `'_original_dpi'` ∈ `state` ⇒ value is `state['_original_dpi']` | R + I | identical in-place assignment of the live-resolution entry to the original-resolution value, under the key-token bijection. This is the behaviour the F2P test observes: `fig2.dpi == 42` (the original), not `42*7` (the scaled value). |
| A4 | `state[key_dpi()] = state[key_dpi()]` (absent branch) | `state["_dpi"] = state.get('_original_dpi', state['_dpi'])` when `'_original_dpi'` ∉ `state` ⇒ value is `state['_dpi']` (the default) | R + I | identical: assigns the live-resolution entry to its own current value (a no-op on the value), mirroring the `.get` default. Modeled explicitly so the deep model is the full `.get`-with-default semantics, not a one-armed conditional. |
| A5 | `Requires(MustTerminate(2))` (totality obligation) | the added hunk is straight-line code inside `__getstate__` — every call returns | R + I | the real operation is loop-free and total on the whole precondition domain, so pinning totality excludes no correct implementation; without it Nagini's partial-correctness default admits a same-spec diverging impl (`while True: pass`) that satisfies every value postcondition vacuously while its real counterpart hangs pickling (and the F2P round-trip) forever — verify ⇏ resolve. Added as an audit (G-PANEL-1) strengthening. |

The `state.get('_original_dpi', state['_dpi'])` primitive (`dict.get` with a
default) is **modeled deeply** — the membership branch (A2) and both arms (A3,
A4) are spelled out in the impl region — so it is an **A-reference**, not a
consumed axiom. There is no `@ContractOnly` axiom; the proof depends on no
callee contract. The deep model's selection semantics is validated against real
Python `dict` (`.get(k, default)` / membership / in-place assignment) by
`axiom_check.py` (G-AX). See §C.

The discriminating content of the change — recording the ORIGINAL resolution
rather than the live (possibly scaled-up) one — lives in clause A3 / the
postcondition `Implies(original_present, state[key_dpi()] == original_value)`.
The pre-patch `__getstate__` omitted the reconciliation entirely;
`model_prepatch.py` reproduces that (an empty impl that leaves `state["_dpi"]`
untouched) and **fails** exactly this postcondition (G-DIFF), which is the spec
sensing the bug.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I (under the key-token / value-token refinement). The
one operation introduced by the change — the `.get`-with-default selection of
which stored DPI to serialize — is modeled **deeply** (the membership branch and
both assignment arms are written out in the impl region), not hidden behind an
axiom. There is no consumed axiom (`A-consumed`): the `axioms` region is empty.

## C. verify(model) ⇒ resolved

`normalize_state_dpi` verifies only if, after it runs, the live-resolution entry
holds the original-resolution value whenever an original-resolution record was
present at entry (clause A3 / postcondition
`Implies(original_present, state[key_dpi()] == original_value)`), and the
recorded value otherwise (A4), with every other entry untouched. By R (`dict` ↔
`Dict[int, int]` with the two key tokens; `float` DPI ↔ `int` token, sound
because the tested behaviour is value-SELECTION not arithmetic — mapping.md §2)
the verified body equals
`state["_dpi"] = state.get('_original_dpi', state['_dpi'])` on the tested input.
By G-AX (`axiom_check.py`) the deep model's `.get`-with-default selection equals
real Python `dict.get`'s. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE: F2P `test_unpickle_with_device_pixel_ratio` expects `fig2.dpi == 42`,
which is exactly clause A3). The only trust point is refinement fidelity (this
document, G-EQ); there is no axiom-soundness trust point because no axiom is
consumed.
