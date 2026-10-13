# mapping.md — matplotlib__matplotlib-22865

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c6c7ec1978c22ae2c704555a873d0ec6e1e2eaa8`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
records callee provenance / flag dependencies.

Repo file under change: `lib/matplotlib/colorbar.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectSegM (segs) (drawEdges) (extLow) (extUp)` | the final `self.dividers.set_segments(...)` statement of `Colorbar._add_solids(self, X, Y, C)` — `lib/matplotlib/colorbar.py:644` (changed statement at body lines 654-655) | the modeled changed function: which divider segments are passed to `set_segments` |
| `selectSeg (segs) (drawEdges) (extLow) (extUp)` | the value built for `set_segments` in the patched branch — `lib/matplotlib/colorbar.py:654-660` post-patch | pure spec: the positional slice of the candidate divider list; concrete (R/I), NOT an axiom/A-reference |
| `startIdx (extLow)` | `start_idx = 0 if self._extend_lower() else 1` — `colorbar.py:657` post-patch | pure spec: lower (inclusive) slice index |
| `endIdx (extUp) (n)` | `end_idx = len(X) if self._extend_upper() else -1` — `colorbar.py:658` post-patch | pure spec: upper (exclusive) slice index |
| `segs : List Seg` | `np.dstack([X, Y])` — `colorbar.py:659` post-patch | the ordered candidate divider list (one entry per mesh boundary row of `X`) |

### 1.1 Scope: what is modeled, and why it suffices

The gold hunk edits exactly one statement of `_add_solids`: the argument passed
to `self.dividers.set_segments(...)`. Pre-patch it was unconditionally
`np.dstack([X, Y])[1:-1] if self.drawedges else []`; post-patch it becomes a
flag-dependent slice (`start_idx`/`end_idx` keyed on `_extend_lower()` /
`_extend_upper()`), or `[]` when `drawedges` is off. Everything earlier in
`_add_solids` (the `solids`/`pcolormesh`/`hatches` artist bookkeeping) is
**unchanged** by the patch and does not affect the value handed to
`set_segments`, so it is outside the modeled operation.

`np.dstack([X, Y])` stacks the two `(len(X) × 2)` coordinate meshes into a
`(len(X) × 2 × 2)` array; indexing its first axis selects whole divider
segments. The modeled operation is purely the **positional selection** of those
segments, so each segment's interior content is opaque to the computation and
is carried as a `List Float` (`Seg`) placeholder. `len(X)` is the number of
candidate boundaries and equals `segs.length`.

The discriminating behavior the FAIL_TO_PASS tests observe is exactly which
boundaries survive: with both ends open all candidates are kept; with only one
end open the boundary at the closed end is dropped; with neither open both end
boundaries are dropped (the legacy `[1:-1]` behavior, which is the
PASS_TO_PASS `neither` case).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) and G-AX use to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `np.dstack([X, Y])`, a `(m × 2 × 2)` float ndarray; first-axis indexing selects whole `(2 × 2)` segments | `segs : List Seg = List (List Float)` | the ndarray `A` ↔ `[A[i].flatten().tolist() for i in range(m)]`; `A.shape[0]` (== `len(X)`) ↔ `segs.length`; first-axis slice `A[s:e]` ↔ `(segs.drop s).take (e - s)` |
| a single divider segment `A[i]` (a `2 × 2` float block) | `Seg = List Float` | `A[i].flatten().tolist()`; opaque to the selection (content never inspected, only position) |
| `self.drawedges : bool` | `drawEdges : Bool` | identity |
| `self._extend_lower() : bool` | `extLow : Bool` | identity — see §3 (flag dependency) |
| `self._extend_upper() : bool` | `extUp : Bool` | identity — see §3 (flag dependency) |
| `start_idx` (`0`/`1`), `end_idx` (`len(X)`/`-1`) | `startIdx extLow : Nat`, `endIdx extUp n : Nat` | Python `end_idx = -1` (closed upper) ↔ `endIdx = n - 1` (exclusive); the negative index `-1` and the exclusive `n-1` denote the same cut point of an `n`-row list, so `A[start:end]` ↔ `(segs.drop s).take (e - s)` |
| `set_segments([])` (drawedges off) | `[] : List Seg` | identity (empty selection) |

No parameter is `mut` (directive 5: the selection mutates nothing; `_add_solids`
reads `X`, `self.drawedges`, and the two `_extend_*` flags, and the modeled
operation produces the divider list — it does not write any of its inputs). The
`mut`-frame obligation is vacuous: every input is read-only and is declared
non-`mut`.

### 2.1 The `-1` vs `n-1` cut point (the one subtle R step)

Python `A[start:end]` with `end = -1` keeps rows `start .. m-2` (drops the last
row); `end = len(X)` keeps rows `start .. m-1` (keeps the last row). The Lean
model uses `endIdx extUp n = if extUp then n else n - 1` with the exclusive
`drop`/`take` slice `(segs.drop s).take (e - s)`. For `extUp = false`,
`e = n - 1`, so `take (n-1-s)` keeps `s .. n-2` — identical to Python `[:-1]`
**for every `n ≥ 1`** (the realizable case: a colorbar always has at least one
boundary). At `n = 0` Python `[s:-1]` and the Lean `take` both yield `[]`, so
the bijection is total. G-CONF fuzzes `n` down to 0/1 to exercise this exactly.

## 3. Callee provenance — NONE (no axioms, no A-references)

The modeled selection calls no unchanged repo function whose contract the proof
must assume:

- **0 consumed axioms.** The `axioms` region of `Solution.lean` is empty.
- **0 A-references.** `selectSeg`/`startIdx`/`endIdx` are concrete positional
  list arithmetic transliterating the numpy first-axis slice (R/I legs), NOT
  deep models of an opaque callee. G-CONF mechanically refutes them.

The two booleans `self._extend_lower()` / `self._extend_upper()` are inputs to
the modeled operation, supplied by the caller as `extLow` / `extUp`. They are
**not** axiomatized: their own computation (`self.extend in ('both', minmax)`
with an inversion swap, `colorbar.py:1352-1360`) is unchanged by the patch and
upstream of the modeled statement, so it is part of the *input*, not the modeled
operation. G-CONF drives the real `_add_solids` end-to-end via a real
`Colorbar`, so the real `_extend_lower`/`_extend_upper` are exercised as-is
through the `extend` configuration — no contract on them is assumed.

`np.dstack`, ndarray first-axis slicing, and `set_segments` are numpy / artist
primitives, not repo callees needing a contract.

### 3.1 Flag dependency (for G-AX / G-CONF fuzz configuration)

`_extend_lower()` / `_extend_upper()` depend on `self.extend ∈ {'neither',
'min', 'max', 'both'}` and on long-axis inversion. G-CONF constructs real
colorbars across all four `extend` values (and `drawedges ∈ {True, False}`) so
both flags take both truth values, covering the full `(drawEdges, extLow, extUp)`
truth table — exactly the FAIL_TO_PASS/PASS_TO_PASS matrix.

## 4. G-CONF / G-AX fuzz seed (pinned for deterministic eval — §4.1, §11.3)

`conformance_check.py` and `axiom_check.py` both seed `random.Random` with
**`22865`** so the consumer-side verdict (§11.3) is reproducible. The R/I shadow
transliterates `startIdx`/`endIdx`/`selectSeg` (all R/I-tagged) to a Python
first-axis slice and compares against the real patched `_add_solids` behaviour
(the divider segments captured from `self.dividers.get_segments()` on a real
`Colorbar`); there is no A-tagged callee to leave as the real repo callee (§3).
