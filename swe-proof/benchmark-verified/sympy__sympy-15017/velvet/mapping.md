# mapping.md — sympy__sympy-15017

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6810dee426943c1a2fe85b5002dd0d4cf2246a05`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
records callee provenance / flag dependencies.

Repo file under change: `sympy/tensor/array/dense_ndim_array.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `arrayLength (dims : List Nat)` | the element count an array exposes via `NDimArray.__len__` (`sympy/tensor/array/ndim_array.py:164`, `return self._loop_size`), where `_loop_size` is set by `ImmutableDenseNDimArray._new` — `dense_ndim_array.py:152` (the line the gold patch edits) | the modeled changed quantity: the total element count derived from the array's shape |
| `prodSeq (dims : List Nat)` | `functools.reduce(lambda x,y: x*y, shape, 1)` — the patched RHS of `self._loop_size` assignment (`dense_ndim_array.py:152` post-patch) | pure spec: product of the dimension sizes with empty product = 1; concrete (R/I), NOT an axiom/A-reference |

### 1.1 Scope: what is modeled, and why it suffices

The gold patch changes one expression in `ImmutableDenseNDimArray._new`
(`dense_ndim_array.py:152`):

```
- self._loop_size = functools.reduce(lambda x,y: x*y, shape) if shape else 0
+ self._loop_size = functools.reduce(lambda x,y: x*y, shape, 1)
```

The byte-identical line also appears in `MutableDenseNDimArray._new`
(`dense_ndim_array.py:177`); the gold patch leaves it untouched, and neither
the issue nor the FAIL_TO_PASS test exercises the mutable subclass, so the
model and the G-CONF oracle bind to the Immutable path only (the patch's actual
behavioral footprint).

`_loop_size` is the array's element count; it is what `__len__` returns
(`ndim_array.py:178`) and what `len(array)` therefore yields. The only
observable behavior the issue and FAIL_TO_PASS test exercise is `len(array)`:

- The issue: `len(sympy.Array(3))` (a rank-0 scalar, shape `()`) returns `0`
  but should return `1` — a scalar holds exactly one element, matching
  `len(list(a)) == 1` and numpy's `asarray(1).size == 1`.
- FAIL_TO_PASS `test_ndim_array_initiation` asserts
  `len(ImmutableDenseNDimArray(x)) == 1` (rank-0) and
  `len(ImmutableDenseNDimArray([], shape=(0,))) == 0` (a `(0,)` shape — product
  is genuinely 0, unchanged by the fix).

`arrayLength` models the value computed for `_loop_size` from `shape`. The
pre-patch expression has a special-case for the empty shape (`if shape else
0`) that yields `0`; the patched expression supplies `1` as the `reduce`
initializer, so the empty shape (no factors) folds to the empty product `1`.
The model captures exactly this: `prodSeq []` = 1 (post-patch), and the
prepatch skeleton reproduces the `else 0` special case. For any non-empty
shape both old and new code agree (the product of the dimensions), so the
single observable discriminator is the empty-shape (rank-0) case — precisely
the issue and the new F2P assertion.

The construction path around `_loop_size` (`_handle_ndarray_creation_inputs`,
`flatten`, `Tuple`, `Basic.__new__`) is NOT on the changed expression: those
build `shape`/`flat_list` and are unchanged by the patch. The model takes the
already-built shape (the `dims` list) as input, which is faithful — the patch
edits only how the count is folded from that shape.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `shape` — a `Tuple` of non-negative integer dimension sizes (`dense_ndim_array.py:151`; each entry a sympified non-negative int) | `dims : List Nat` | `shape` ↔ `dims`: the i-th dimension size ↔ `dims[i]`; `len(shape)` (the rank) ↔ `dims.length`; each dimension is a non-negative integer ↔ `Nat` |
| `functools.reduce(lambda x,y: x*y, shape, 1)` (post-patch product with initializer 1) | `prodSeq dims` | `reduce(mul, shape, 1)` over a finite tuple ↔ the front-recursive product fold `prodSeq`; identical associative-commutative product, empty fold = `1` |
| `self._loop_size` / `len(array)` (the returned element count, a non-negative int) | `n : Nat` | exact integer equality: `len(array)` ↔ `n` |

Observable-equality predicate (plan §10 Q5b): exact natural-number equality on
the element count. No tolerance — `_loop_size` is an exact integer.

`dims` is read-only: it is not declared `mut` (directive 5 — `arrayLength` is a
pure fold of the shape; nothing is mutated). The dimension sizes are
non-negative by construction (a numpy/sympy shape never has negative entries),
so `Nat` is a sound carrier; the product fold needs no `require`.

## 3. Callee provenance — NONE (no axioms, no A-references)

The changed expression calls only `functools.reduce` with a multiplication
lambda over the already-built `shape` tuple. There is **no unchanged repo
callee** whose contract the proof must assume, so:

- **0 consumed axioms.** The `axioms` region of `Solution.lean` is empty.
- **0 A-references.** `prodSeq` is the concrete product fold transliterating
  `reduce(mul, shape, 1)` (an R/I leg), NOT a deep model of an opaque callee.
  G-CONF mechanically refutes it. There is therefore **no `axiom_check.py`**:
  with no consumed axiom and no A-reference, G-AX has nothing to falsify and
  skips (the canonical 0-axiom pattern). Note also that G-AX runs the bundle's
  checker against the *unpatched* container — so any "axiom_check" comparing
  `prodSeq` to the real `len()` would be testing the model against the *buggy*
  pre-patch behavior (rank-0 shape → `len()==0`) and would fail by construction
  on exactly the case the patch fixes. The model↔patched-`len()` agreement is
  instead exercised by G-CONF, which applies the gold patch first.

`__len__` (`ndim_array.py:164`) is an unchanged trivial accessor
(`return self._loop_size`); it is not axiomatized because it performs no
computation — it merely surfaces the modeled value, and the bijection in §2
treats `len(array)` as the observation of `n`. The siblings
`_handle_ndarray_creation_inputs`, `flatten`, `Tuple`, `_sympify` build the
shape/data and are not on the changed expression's data path (they produce the
`shape` the model takes as input), so they need no axiomatization.

No flag-dependent callees.

## 4. G-CONF fuzz seed (pinned for deterministic eval — §4.1, §11.3)

`conformance_check.py` seeds `random.Random` with **`15017`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`prodSeq` (the only impl computation, R/I-tagged) to Python and compares
against the real patched `len(NDimArray(...))` at base_commit (G-CONF applies
the gold patch first); there is no A-tagged callee to leave as the real repo
callee (§3), and no `axiom_check.py` (G-AX skips — 0 axioms).
