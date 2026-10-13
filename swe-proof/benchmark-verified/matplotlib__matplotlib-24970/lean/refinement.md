# refinement.md — matplotlib__matplotlib-24970

Operation correspondence between `implementation_index` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the changed behavior — recording each
out-of-range value's reserved lookup-table slot index *exactly*, independently
of the input value type's capacity — is modeled DEEPLY. Every row is **R**,
**A-reference**, or **I**. The R/I/A-reference legs are differential-tested by
G-CONF; G-AX is a skip stub (no consumed callee axiom).

## The fix

`Colormap.__call__` converts data values into row indices of a lookup table
(LUT) with `N + 3` rows (palette rows `0..N-1`, then `under = N`, `over = N+1`,
`bad = N+2`). The out-of-range assignments are

```python
xa[xa > self.N - 1] = self._i_over     # = N + 1
xa[xa < 0]          = self._i_under    # = N
xa[mask_bad]        = self._i_bad      # = N + 2
```

Pre-patch, for an **integer-dtype** input the index array `xa` kept the input's
own (possibly narrow) dtype, because the widening cast `xa = xa.astype(int)`
lived *inside* the `if xa.dtype.kind == "f":` (float-only) branch. Assigning a
reserved slot number (e.g. `N + 1 = 257`) into a narrow integer array
(e.g. `uint8`, capacity 256) cannot be done faithfully — NumPy ≥ 1.24 rejects
the out-of-bound store (a `DeprecationWarning` that the test suite, run with
`filterwarnings = error`, turns into a hard failure). The gold patch hoists the
cast out so it runs for **all** dtypes before the reserved-slot assignments:

```python
with np.errstate(invalid="ignore"):
    # We need this cast for unsigned ints as well as floats
    xa = xa.astype(int)
```

so the index container is always wide enough to hold `N + 2` and the conversion
always succeeds.

## Type model (mapping.md)

* the integer data values → `xs : List Int`;
* the palette size `self.N` → `N : Nat`; reserved slots `under = N`,
  `over = N + 1`;
* the input value type's capacity → `M : Nat` (a `uintW`/native int holds
  `0 … M - 1`; for `uint8`, `M = 256`);
* the result index array → `Except Unit (List Nat)`: `Except.ok` carries the
  exact LUT row indices; `Except.error` models the rejected out-of-bound store.

## `implementation_index` ↔ the integer-indexing path of `__call__`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `for x in xs do …` accumulating `out` | element-wise processing of the index array `xa` | I | one output index per input value |
| `let mut idx := x` | `xa` starts as the (integer) data values | I | identity carry |
| `if idx > (N:Int) - 1 then idx := N + 1` | `xa[xa > self.N - 1] = self._i_over` (`= N + 1`) | A-reference | over-slot assignment; modeled deeply as the exact index `N + 1` |
| `if idx < 0 then idx := N` | `xa[xa < 0] = self._i_under` (`= N`) | A-reference | under-slot assignment; exact index `N` (note: applied after the over-test, matching the source comment "Set the over-range indices before the under-range") |
| `out := out ++ [idx.toNat]` | the reserved index is stored into `xa` | A-reference | POST-PATCH: the wide index container records `N` / `N+1` exactly; the EDITED behavior. PRE-PATCH the narrow container of capacity `M` rejects an index `≥ M` |
| `return Except.ok out` | the conversion completes without error | R | success ↦ `Except.ok`; pre-patch out-of-bound store ↦ `Except.error` |

The result observable is the list of LUT row indices; the real callee then does
`lut.take(xa, …)`, so an index of `N` / `N+1` selects the dedicated under/over
color row. G-CONF bridges index → color through the real LUT and confirms the
modeled mapping equals the real patched `Colormap.__call__` over the boundary
catalogue + ≥1e5 fuzzed integer inputs.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the index container keeps the input value type's
  capacity `M`; assigning a reserved slot number `≥ M` is rejected
  (`return Except.error ()`) rather than recorded. The carried gold proof of
  `correct_index` fails to close: whenever `N + 1 ≥ M` (e.g. `N = 256`,
  `M = 256`, the default-palette / `uint8` case the issue reports) and an input
  value is out of range, the impl returns `Except.error`, contradicting the
  spec's `∃ out, result = Except.ok out`. This is the single fixed behavior.
  (FAIL_TO_PASS: `test_index_dtype[uint8]`.)
