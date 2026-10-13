# mapping.md — matplotlib__matplotlib-24970

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a3011dfd1aaa2487cce8aa7369475533133ef777`, states the type
abstraction, and gives the provenance + executable-soundness obligation of the
one axiomatized callee.

Repo file under change: `lib/matplotlib/colors.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `take_rows(values, bads, n, modulus)` | `Colormap.__call__` — `lib/matplotlib/colors.py:683` (the integer index-resolution stage, body lines 715–738) | the modeled changed function: maps each element to its final lookup-table row |
| `assign_special_rows(values, bads, n, modulus)` *(@ContractOnly — A-consumed)* | the UNCHANGED per-element special-row assignment: the three sequential stores `xa[xa > self.N-1] = self._i_over` / `xa[xa < 0] = self._i_under` / `xa[mask_bad] = self._i_bad` (`colors.py:730–732`) followed by `lut.take(xa, axis=0, mode='clip')` (`colors.py:738`), carried out on the integer container of `xa` | callee: performs the array special-row assignment; well-defined only on a container that admits every special index it writes |
| `rows_assigned(rows, n)` *(@ContractOnly @Predicate)* | the capability that the special-row assignment COMPLETED (the stores were in-range for the container) — there is no repo identifier for it; it abstracts the "assignment carried out without an out-of-range store" effect | unforgeable token granted only by a well-defined `assign_special_rows`; required by the result of `take_rows` |
| `selected_index(v, n, bad)` | which lookup row one element selects (the precedence of the three stores in `colors.py:730–732`) | pure spec |
| `clip_row(idx, n)` | the `mode='clip'` index clamp of `lut.take` (`colors.py:738`) | pure spec |
| `final_row` / `rows_of` | the composition of the above over the whole array | pure spec: the per-element / whole-array row result |

The special-row indices come from `Colormap.__init__` (`colors.py:673–675`):
`self._i_under = self.N`, `self._i_over = self.N + 1`, `self._i_bad = self.N + 2`;
and the lookup table has `self.N + 3` rows (`colors.py:1008/1164`,
`self._lut = ...((self.N + 3, 4) ...)`), so rows `N`, `N+1`, `N+2` are valid and
distinct. `N >= 1` (`self.N = int(N)`, default 256).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `xa = np.array(X)`, the per-element integer index values (post float-scaling for float inputs; the raw integer values for integer inputs) | `values: List[int]` | `values[k]` ↔ the integer value of `xa.flat[k]`; element-wise NumPy ops ↔ the per-element model |
| `mask_bad` boolean array (`colors.py:711–714`) | `bads: List[bool]` | `bads[k]` ↔ `mask_bad.flat[k]` |
| `self.N` (number of ordinary colour rows) | `n: int`, `n >= 1` | identity |
| the input array's integer **dtype range** — the set of values its container admits exactly (a dtype admitting `k` distinct values represents the largest value `k-1` for unsigned; an unsigned m-bit dtype admits `0 .. 2**m - 1`) | `modulus: int`, `modulus >= 1` (admits `0 .. modulus-1`) | unsigned dtype of `2**m` distinct values ↔ `modulus = 2**m`; the post-patch signed-`int` carrier ↔ a `modulus` larger than every written index (`>= N+3`) chosen in the impl |
| `with np.errstate(...): xa = xa.astype(int)` (the cast moved out of the float branch) | the carrier-width choice `carrier = max(n+3, modulus)` in `take_rows` impl | the cast to `int` produces a container admitting every special index `<= N+2`; modelled by choosing a carrier whose admitted range exceeds every written index |
| `lut.take(xa, mode='clip')` (`colors.py:738`) | `clip_row` applied per element (inside `assign_special_rows`'s result spec) | `mode='clip'` clamps each index to `0 .. len(lut)-1 = N+2` |

`X` may be a scalar, the array, or a masked array; the modeled stage operates
element-wise after `xa = np.array(X, copy=True)`, so the per-element / sequence
model is exact for every shape (the F2P test passes the scalar `dtype(0)`; a
length-1 sequence in the model).

## 3. Axiom provenance + soundness (the A-consumed callee + its token)

`assign_special_rows` is the **only** `@ContractOnly` callee, and it is
**A-consumed** (the proof of `take_rows` uses its `Ensures` — both the
per-element row result and the `rows_assigned` token). It models the UNCHANGED
NumPy special-row assignment; it is NOT the function under change. The token
`rows_assigned` is `@ContractOnly @Predicate` so it cannot be folded into
existence by an impl and (carrying the produced rows + `n`) cannot be laundered
across a value-equal copy.

The contract makes two claims, both validated against real NumPy by
`axiom_check.py` (G-AX), which imports only the standard library + `numpy`
(the dependency the patch operates on) and exits 0 iff sound:

### 3.1 RESULT — `Ensures(ToSeq(Result()) == rows_of(...))`
On a well-defined assignment, each element's row is
`final_row(v,n,bad) = clip_row(selected_index(v,n,bad), n)`:
```python
with np.errstate(invalid="ignore"):
    xa = xa.astype(int)                 # carrier admits every special index
xa[xa > self.N - 1] = self._i_over      # N+1, over-range
xa[xa < 0]          = self._i_under     # N,   under-range
xa[mask_bad]        = self._i_bad       # N+2, bad/masked (last ⇒ highest prec.)
row = lut.take(xa, axis=0, mode='clip') # clamp to 0..N+2
```
G-AX asserts `final_row == real_row_widened` on 48 boundary + 20000 fuzz
`(v,n,bad)` triples (`axiom_check.check_result_on_widened`).

### 3.2 LEGALITY PRECONDITION — `Requires(modulus >= n+3)` (the load-bearing claim)
The largest special index written is `N+2`; an integer container admits it iff
its representable maximum is `>= N+2`, i.e. (for a container admitting
`0..modulus-1`) `modulus-1 >= N+2`, i.e. `modulus >= N+3`. This is exactly the
condition under which the special-row stores complete WITHOUT an out-of-range
conversion — i.e. without NumPy's out-of-bound-integer `DeprecationWarning`,
which matplotlib's pytest config (`filterwarnings=error`) escalates to the F2P
failure. Crucially the store's scalar→dtype conversion is evaluated regardless
of whether any element matches the mask, so the deprecation fires even for the
unmasked value-0 F2P input.

G-AX (`axiom_check.check_legality_precondition`) asserts, against real NumPy,
that for `dtype ∈ {uint8, uint16, int8, int16}` sweeping `N` across the
`n+2 = max` threshold: the special-row stores on the F2P-shaped input (value 0,
unmasked) emit a `DeprecationWarning` **iff** the largest special index does NOT
fit the container — i.e. "no deprecation" coincides EXACTLY with `n+2 <= max`,
which for unsigned dtypes is `modulus >= n+3`. So `modulus >= n+3` is neither too
strong (no admitting width is excluded) nor too weak (every excluded width
really warns). The witness (`axiom_check.check_f2p_witness`) pins the exact F2P
case: uint8, `N=256` (`modulus 256 < 259`) deprecates on `cm(uint8(0))` while a
widened carrier does not, value unchanged (row 0).

### 3.3 `clip_row` ↔ `lut.take(..., mode='clip')`
`numpy.take(a, indices, mode='clip')` clamps each index into `0 .. a.shape[0]-1`.
The table has `N+3` rows, so the clamp range is `0 .. N+2`, exactly `clip_row`.
Folded into the §3.1 result check. Docs:
https://numpy.org/doc/stable/reference/generated/numpy.take.html.

**Soundness check (G-AX):** `axiom_check.py` reconstructs the real NumPy special-
row assignment and asserts (1) the widened-carrier result == `final_row` (48
boundary + 20000 fuzz); (2) `modulus >= n+3` coincides EXACTLY with the
no-deprecation legality across uint8/uint16/int8/int16 around the threshold;
(3) the F2P witness (uint8 N=256 deprecates on the unmasked value-0 input; a
widened carrier does not; value unchanged). Exit 0 iff sound. Confirmed RC=0 in
the pinned eval container (numpy 1.25.2).
