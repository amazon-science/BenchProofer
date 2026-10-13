# refinement.md — matplotlib__matplotlib-24970

The operation-by-operation correspondence between `model.py`'s implementation
(the `take_rows` impl region, the @ContractOnly callee `assign_special_rows` and
its capability token `rows_assigned`, and the deep pure models `selected_index`
/ `clip_row` / `final_row` / `rows_of`) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, the proof uses the axiom's `Ensures`, and **A-reference**, a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## 0. What the F2P test actually observes (the discriminator)

The sole F2P test is `test_index_dtype[uint8]`:
`assert_array_equal(cm(np.uint8(0)), cm(0))`, run under matplotlib's pytest
config (`filterwarnings = error`). The data value is **0**, unmasked, with the
default `N = 256`. The *colour value* of `cm(np.uint8(0))` is **identical**
pre- and post-patch (row 0) — confirmed in the pinned container. The test fails
pre-patch NOT on a value difference but because the special-row assignment
statements
```
xa[xa > self.N - 1] = self._i_over   # store the scalar 257 into xa's container
xa[xa < 0]          = self._i_under  # store 256
xa[mask_bad]        = self._i_bad    # store 258
```
convert the special-index scalars (`N+1=257`, `N=256`, `N+2=258`) into `xa`'s
uint8 container, which emits NumPy's out-of-bound-integer **DeprecationWarning**
— and this conversion is evaluated regardless of whether any element matches the
mask (here none does). pytest escalates the warning to a failure. The gold fix
casts `xa` to a signed `int` (a wide container that admits every special index)
BEFORE those stores, so the conversion is in-range and no warning is emitted.

The discriminator is therefore a **side-effect of the assignment statement**
(out-of-range store vs. in-range store), present on the F2P input even though
the result value is unchanged. There is no value-level discriminator on the F2P
input, so the spec cannot be pinned to a value property alone (a buggy
narrow-carrier impl returns the same row values). The discriminator is modelled
as an unforgeable capability token (§A) granted only when the assignment is
carried out on a container that admits every special index it writes.

## A. The index-resolution site — `Colormap.__call__` (`lib/matplotlib/colors.py:683`)

Gold hunk (`colors.py:715–732`): the `xa = xa.astype(int)` cast is moved OUT of
the `xa.dtype.kind == "f"` branch so it runs for EVERY dtype, BEFORE the three
special-row writes:
```
  if xa.dtype.kind == "f":
-     with np.errstate(invalid="ignore"):
-         xa *= self.N
-         xa[xa < 0] = -1
-         xa[xa == self.N] = self.N - 1
-         np.clip(xa, -1, self.N, out=xa)
-         xa = xa.astype(int)
+     xa *= self.N
+     xa[xa < 0] = -1
+     xa[xa == self.N] = self.N - 1
+     np.clip(xa, -1, self.N, out=xa)
+ with np.errstate(invalid="ignore"):
+     # We need this cast for unsigned ints as well as floats
+     xa = xa.astype(int)
  xa[xa > self.N - 1] = self._i_over
  xa[xa < 0] = self._i_under
  xa[mask_bad] = self._i_bad
```

| # | model.py impl op (`take_rows`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `values: List[int]` | the per-element integer values of `xa = np.array(X)` | R | NumPy integer array ↔ `List[int]` element-wise (mapping.md §2). |
| A2 | parameter `bads: List[bool]` | `mask_bad` boolean array (`colors.py:711–714`) | R | NumPy bool array ↔ `List[bool]` element-wise. |
| A3 | parameter `n: int` | `self.N` | R | identity (`self.N = int(N)`). |
| A4 | parameter `modulus: int` (the range of values the INPUT integer container admits) | the integer dtype range of `xa` (the input dtype, before any cast) | R | a dtype admitting `k` distinct values ↔ `modulus = k`; an unsigned m-bit dtype ↔ `modulus = 2**m` (mapping.md §2). |
| A5 | the per-element materialization loop building `sel_values` / `sel_bads` (`ToSeq(sel_values) == ToSeq(values)`, `ToSeq(sel_bads) == ToSeq(bads)`) | `xa = np.array(X, copy=True)` (`colors.py:716`) and the element-wise boolean `mask_bad` — the array the special-row writes operate over | R | the array is materialized element-by-element; the model rebuilds the per-element value/mask sequence the assignment ranges over. The loop is faithful to the element-wise array; its index arithmetic carries no behaviour beyond reproducing the input sequence. |
| A6 | `carrier = n + 3` (carry out the assignment on a container that admits up to `n + 2`, the largest special index) | `with np.errstate(invalid="ignore"): xa = xa.astype(int)` — the cast moved out of the float branch so it runs for ALL dtypes BEFORE the special-row writes | R | the cast-to-`int` produces a container that admits every special index (`int` represents any value `<= N+2`); modelled as choosing a carrier whose admitted range covers every written index (`carrier = n + 3` admits `0 .. n + 2`). The cast itself is the unchanged NumPy `astype`; the refinement is the carrier-width choice. |
| A7 | `result = assign_special_rows(sel_values, sel_bads, n, carrier)` | `xa[xa > self.N-1] = self._i_over`; `xa[xa < 0] = self._i_under`; `xa[mask_bad] = self._i_bad`; then `lut.take(xa, axis=0, mode='clip')` (`colors.py:730–732,738`) | A-consumed | the unchanged per-element special-row assignment over the array (the three sequential conditional stores in order, same constants `_i_over=N+1`, `_i_under=N`, `_i_bad=N+2` from `__init__`, then the `mode='clip'` gather). The proof CONSUMES this callee's `Ensures`: the per-element result is `rows_of(...)` AND the assignment grants the `rows_assigned` token — but the `Ensures` applies only when the carrier admits every special index (`Requires(modulus >= n+3)`), exactly the legality of the store. Validated == the real NumPy operation by G-AX (mapping.md §3). |

The discriminating content of the change — the special-row assignment **must be
carried out on a container that admits every index up to `N + 2`** — lives in
the interaction of A6 and A7: `take_rows` may only call `assign_special_rows`
(and so obtain the `rows_assigned` token its postcondition requires) once it has
established `carrier >= n+3` (A6). The gold patch establishes this by casting to
`int`. The pre-patch keeps the input dtype for the special-row writes;
`model_prepatch.py` reproduces that by calling `assign_special_rows(sel_values,
sel_bads, n, modulus)` with the input's own (possibly narrow) `modulus`, which
does NOT satisfy the callee precondition `modulus >= n+3` for a narrow container
(e.g. uint8 `modulus=256`, `N=256`): the assignment is not well-defined, the
token is never granted, so the postcondition `rows_assigned(...)` cannot be
discharged and verification **fails** — exactly the spec sensing the change
(G-DIFF). The token is unforgeable: it is `@ContractOnly @Predicate` so an impl
cannot `Fold` it into existence, and it carries the produced rows + `n` so it
cannot be laundered across a value-equal copy.

## B. No kind-3 (unexpressible-changed-op) steps

Every step is R or A. The one operation that genuinely *changed* — widening the
integer container before the special-row writes — is captured by the
combination of the carrier-width refinement (A6) and the callee's legality
precondition (A7: the assignment is well-defined, and grants its token, only on
a container admitting every special index). The assignment itself
(`assign_special_rows`) is an UNCHANGED NumPy operation invoked by both twins;
it is **A-consumed** (the proof uses its `Ensures` — both the row result and the
token) and validated against the real NumPy operation by G-AX. There is no axiom
about the function under change, and no kind-3 step.

## C. verify(model) ⇒ resolved

`take_rows` verifies only if it produces a result holding the unforgeable
`rows_assigned(ToSeq(Result()), n)` token. That token is obtainable ONLY from
`assign_special_rows`, whose `Ensures` grants it ONLY under
`Requires(modulus >= n+3)` — a container that admits every special index it
writes. So a verifying impl must route its result through an assignment carried
out on an admitting (widened) container; it cannot return a row sequence that a
narrow-carrier assignment produced, even though the row values would be
identical. The gold patch establishes `modulus >= n+3` by casting to a signed
`int` for ALL dtypes before the writes (A6); by R (NumPy array ↔ `List`,
`self.N ↔ n`, dtype range ↔ `modulus`) and by G-AX (the assignment's row result
== `final_row` over the array, and `modulus >= n+3` coincides EXACTLY with the
real "no out-of-bound deprecation" legality), the verified resolver equals the
gold patch's integer pipeline on the tested inputs AND performs the special-row
stores only on a container that admits them (no deprecation).

The F2P test `cm(np.uint8(0)) == cm(0)` (run under `filterwarnings=error`)
exercises exactly this: pre-patch the uint8 carrier (`modulus=256 < N+3=259`)
makes the special-row stores out-of-range → deprecation → test failure
(model_prepatch fails to obtain the token); post-patch the widened carrier
admits them → no deprecation → test passes (model.py grants and requires the
token), with the value unchanged (row 0 either way). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and one audited A-consumed callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX: the `assign_special_rows` contract, including its weakest-sufficient
legality precondition, over-approximates the real NumPy operation) and
refinement fidelity (this document, G-EQ).
