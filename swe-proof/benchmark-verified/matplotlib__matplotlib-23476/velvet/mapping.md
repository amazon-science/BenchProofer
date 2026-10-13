# mapping.md — matplotlib__matplotlib-23476

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 33a0599711d26dc2b79f851c6daed4947df7c167`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of every modeled value. There are **no axioms and no A-references**:
the step under spec calls no outside routine; its whole effect is the in-place
selection of one resolution value from values already present in the assembled
serialized state.

Repo file under change: `lib/matplotlib/figure.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `finalizeSnapshot (snap : SurfaceSnapshot)` | `Figure.__getstate__` — `lib/matplotlib/figure.py:3015` (added line at `figure.py:3026`, the tail before the version stamp) | the modeled changed function: the serialization hook that assembles the picklable state mapping |
| `snap.resolution` | `state['_dpi']` — the working dots-per-inch value already copied into `state` by `super().__getstate__()` (`Artist.__getstate__`, `lib/matplotlib/artist.py:186`, `self.__dict__.copy()`) | the resolution the snapshot currently carries |
| `snap.baseline` | `state.get('_original_dpi', …)` — the optional `_original_dpi` entry of `state`; set on the figure by the canvas at `lib/matplotlib/backend_bases.py:1656` (`figure._original_dpi = figure.dpi`) and present in `state` iff it was ever set | the recorded reference resolution; `Option Float` (`some` ⇔ the key is present, `none` ⇔ absent) |
| `snap.payload` | every other entry of the `state` dict (`_cachedRenderer`, the figure attributes, …) the hook does not touch on the added line | the opaque remainder of the assembled snapshot |
| `SurfaceSnapshot` | the in-progress `state` dict returned by `__getstate__` | the serialized snapshot, abstracted to the touched/observed fields |

The pre-patch repo behaviour the change corrects (refinement audit only, not in
the consumer spec view): `__getstate__` persisted `state['_dpi']` as it stood —
i.e. the *doubled* working dpi a high-pixel-ratio canvas had written via
`backend_bases.FigureCanvasBase._set_device_pixel_ratio` (`dpi = ratio *
figure._original_dpi`, `backend_bases.py:2104-2105`). Reloading then redoubled
it, so repeated round-trips grew the dpi without bound.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `state['_dpi']` (a `float`, the dpi) | `Float` (`resolution`) | identity; IEEE-754 double ↔ Lean `Float`. Both `_dpi` and `_original_dpi` are plain dpi floats, only their *selection* matters — no arithmetic is performed — so order/equality is all the spec observes. |
| `state.get('_original_dpi', d)` — key present vs absent | `Option Float` (`baseline`) | `some v` ⇔ `'_original_dpi' in state` with value `v`; `none` ⇔ key absent. `dict.get(k, d)` ⇔ `(opt).getD d`. |
| the rest of the `state` dict | `List Char` (`payload`) | opaque carrier; the added line writes only `state['_dpi']`, so every other entry is observably unchanged. The carrier type is immaterial (any `Inhabited` type with decidable equality works); `List Char` is used as a concrete stand-in. The frame clause `out.payload = snap.payload` pins "nothing else changed." |

`state['_dpi']` is always present after `super().__getstate__()` (it is a real
attribute of every `Figure`), so the default branch of `dict.get` is well-typed:
`snap.resolution` is the value supplied as the `dict.get` default.

## 3. Callee provenance

None. The added line `state["_dpi"] = state.get('_original_dpi', state['_dpi'])`
performs a pure dictionary read and write over values already in `state`; it
invokes no repository or stdlib routine whose behaviour must be axiomatized or
deeply modeled. Hence `meta.json axioms = []`, `deep_model_references = []`, and
**G-AX is skip** (no `axiom_check.py`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`23476`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `finalizeSnapshot` (`out.resolution = baseline.getD resolution`,
`baseline`/`payload` preserved) to Python and diffs it against `patch.diff`'s
behaviour: both the verbatim patched expression over fuzzed `(state dict)` inputs
and a live anchor — a real `Figure` whose canvas had its device pixel ratio
raised — pickled through the patched `__getstate__`, confirming the persisted
`_dpi` equals `_original_dpi` and that no other state entry is disturbed.
