# mapping.md — pydata__xarray-7233

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 51d37d1be95547059251076b3fadaa317750aab3`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the one neighbouring callee the model relies on.

Repo file under change: `xarray/core/rolling.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `coordsToKeep (requestedDims coordNames : List String)` | the coordinate re-selection of `Coarsen.construct` — `xarray/core/rolling.py:973` (the `should_be_coords = …` statement, body of `construct`) | the modeled changed function: which prior names remain coordinates after the reshape |
| `keptCoordNames` *(pure deep model)* | the right-hand side the patched statement computes — `(set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)` (`rolling.py:976-978` post-patch) | pure spec: the chosen coordinate-name set |
| `requestedDims : List String` | `set(window_dim)` — the keys of the `window_dim` mapping passed to `construct` (`rolling.py:923`, used at `:976`) | names of the dimensions being reshaped |
| `coordNames : List String` | `set(self.obj.coords)` — the prior coordinate names of the container (`rolling.py:976`) | prior coordinate-name set |
| *(A-reference, not a Lean symbol)* | `reshaped.set_coords(should_be_coords)` — `rolling.py:979`; `Dataset.set_coords` at `xarray/core/dataset.py:1683` | UNCHANGED callee that installs the chosen name-set as the result's coordinates; identity on the coordinate-name set (G-AX) |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): `should_be_coords = set(window_dim) & set(self.obj.coords)`
(`rolling.py:976` pre-patch) — the intersection that drops non-dimensional
coordinates.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a set of variable/coordinate names (`set[str]`, e.g. `set(self.obj.coords)`, `set(window_dim)`) | `List String` | a Python name-set `S` ↔ any `List String` whose elements are exactly `S` (membership is the only observable; order and duplicates are irrelevant — `coordsToKeep`'s spec is stated purely as `k ∈ out ↔ k ∈ coordNames`) |
| `&` (set intersection), `|` (set union) on name sets | `List.filter (·.contains)` / `++` | `{k for k in A if k in B}` ↔ `A.filter (fun k => B.contains k)`; `A | B` ↔ membership-union (here realised as `A ++ B`) |
| `set(self.obj.coords)` of the result Dataset | `out` (the returned `List String`) | observed via `set(result.coords)`; G-CONF reads the genuine post-`construct` coordinate names |

Only the resulting SET of coordinate names is observed; the F2P test asserts
`list(da.coords) == list(result.coords)` as sets of names, so `List String` with
membership semantics is the faithful, minimal carrier.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `set_coords` name identity (A-reference)
**Callee:** `xarray.core.dataset.Dataset.set_coords(names)` (`dataset.py:1683`).
The modeled operation computes a chosen coordinate name-set and hands it to
`reshaped.set_coords(...)`. The deep model treats the result's coordinate names
as exactly that chosen set — i.e. `set_coords` is an identity on the
coordinate-name set (it only flips the coordinate flag on existing variables;
`obj._coord_names.update(names)` on a freshly rebuilt, otherwise coordinate-free
`reshaped`). This is an UNCHANGED callee; the patch does not touch it.

**Soundness check (G-AX):** `axiom_check.py` runs the real `Dataset.set_coords`
on coordinate-free Datasets over boundary + 2000 randomized `(variables, chosen)`
configurations and asserts `set(result.coords) == set(chosen)`. It additionally
confirms the pure set-algebra identity the deep model encodes,
`(requestedDims ∩ coordNames) ∪ coordNames == coordNames`, over boundary + 20000
fuzz pairs. Imports only the repo's own `xarray`/`numpy`. Exit 0 iff sound.

No consumed axioms: the proof uses no callee's `ensures`; the changed string-set
operation is modeled deeply (`keptCoordNames`) and the only callee fact is the
A-reference above, validated == the real callee by G-AX.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7233`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `coordsToKeep`'s set ops to Python (`{k for k in requestedDims
if k in coordNames} | set(coordNames)`) and leaves the reshape + coordinate
installation as the REAL repo path (`coarsen(...).construct(...)`), reading back
`set(result.coords)` as the oracle (A-tagged callee → run real callee, not a
model).
