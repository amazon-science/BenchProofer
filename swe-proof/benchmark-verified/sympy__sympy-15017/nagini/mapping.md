# mapping.md — sympy__sympy-15017

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6810dee426943c1a2fe85b5002dd0d4cf2246a05`, states the type
abstraction, and gives the provenance of the modeled behaviour.

Repo file under change: `sympy/tensor/array/dense_ndim_array.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `array_element_count(shape)` | the `self._loop_size = …` assignment in `ImmutableDenseNDimArray._new(cls, iterable, shape, **kwargs)` — `sympy/tensor/array/dense_ndim_array.py:152` | the modeled changed computation: the array's stored-element count, computed from `shape` and reported by `NDimArray.__len__` |
| `axis_count(shape, k)` | the running product `functools.reduce(lambda x,y: x*y, shape, 1)` (post-patch) over the axis lengths | pure spec: product of the first `k` axis lengths; base case (no axes) is the empty product 1 |
| `lemma_axis_count_unfold` | (proof scaffold only — no repo counterpart) | exposes the one-step recursion of `axis_count` to the impl loop |

### Why `array_element_count` is the right modeled unit
`NDimArray.__len__` (`sympy/tensor/array/ndim_array.py:164-178`) is literally
`return self._loop_size`; it carries no logic of its own. The entire observable
content of the fix lives in how `_loop_size` is computed in `_new`. The F2P test
`test_ndim_array_initiation` observes this through `len(...)`:

- `len(ImmutableDenseNDimArray([], shape=(0,))) == 0` — shape `(0,)`, product `0`.
- `len(ImmutableDenseNDimArray([23])) == 1` — shape `(1,)`, product `1`.
- `len(ImmutableDenseNDimArray(range(3**4), (3,3,3,3))) == 81` — product `81`.
- `len(ImmutableDenseNDimArray(x)) == 1` — rank-zero scalar, shape `()`, the
  **empty product 1** (the pre-patch value was `0`; this is the bug the issue
  reports). The follow-on assertion `rank_zero_array[0] == x` is a *downstream
  consequence* of the same `_loop_size` value: `_parse_index` (ndim_array.py:66-69)
  raises iff `index >= self._loop_size`, so `0 >= 1` is now False and the lookup
  succeeds. The gold patch changes only `_loop_size`; that single change drives
  both observations.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `shape` — a `sympy.Tuple` of sympified non-negative-integer axis lengths (built at `dense_ndim_array.py:149`; for a concrete array every entry is an `Integer`) | `List[int]` of axis lengths | `shape[k]` (the k-th axis length) ↔ `shape[k]`; `len(shape)` (number of axes = the array rank) ↔ `len(shape)`; the empty `Tuple()` (rank-zero scalar) ↔ `[]` |
| `shape` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `len`/`[i]` mirror the tuple's `len`/index |
| `functools.reduce(lambda x,y: x*y, shape, 1)` — left fold with initial value `1` (post-patch) | the prefix-recursive `@Pure` `axis_count(shape, len(shape))` | `reduce(mul, shape, 1)` = `1 * shape[0] * … * shape[k-1]`; `axis_count(shape, 0) == 1` (empty product), `axis_count(shape, k) == axis_count(shape, k-1) * shape[k-1]`. The two compute the same integer for every `shape`. |
| integer `int` of sympy/`functools` arithmetic | Python/Viper `int` | products of axis lengths are exact integers; no precision concern (refinement.md R0) |

`sympy.Tuple`/`Integer` indexing and `functools.reduce` are not Nagini
expressible, so the carrier is `List[int]` and the fold is spelled out as a
prefix-recursive pure product whose base case is `1`.

## 3. Axioms / callee provenance

**None.** The only operation the fix changes is the running product of the axis
lengths with the empty-product convention `reduce(mul, shape, 1)`. That is pure
integer arithmetic, modeled **deeply** by the prefix-recursive `@Pure`
`axis_count` (no opaque library callee is invoked or relied on inside the
specification). There is therefore no `@ContractOnly` axiom (A-consumed) and no
deep-model-vs-real-callee equivalence to validate (A-reference): no
`axiom_check.py` is shipped, and G-AX has nothing to check. `functools.reduce`
is the standard left-fold and is reproduced exactly by the fold's defining
equation; `__len__` is the identity `return self._loop_size`.

## G-CONF (differential conformance)

`conformance_check.py` refutes the R/I refinement leg — the one leg no other
gate covers: does the MODEL agree with the REAL patched repository code?
(G-VERIFY checks impl-vs-spec, G-PBT checks spec uniqueness; neither imports
sympy.)

- **Shadow.** The `# impl-start` / `# impl-end` region of `model.py` copied
  **verbatim**, with only the contract calls deleted: the `Invariant(...)` block
  between `# invariants-start` / `# invariants-end` and the two `Assert(...)`
  lines. The `@Pure` region (`axis_count`, `lemma_axis_count_unfold`) is copied
  the same way, minus `@Pure` and its `Requires`/`Ensures`. Nothing is renamed,
  reordered or simplified. Verbatim-ness is **machine-checked at run time**, not
  asserted: `_check_shadow_verbatim()` parses the mounted `model.py`, strips
  docstrings + contract statements from the ASTs of the three functions, and
  requires `ast.dump` equality with this script's copies — a paraphrased shadow
  fails before the differential runs. Carrier shim: `PSeq`/`ToSeq` (§2, row 2).
  No `@ContractOnly` callee to redirect (§3: the fold is modeled deeply, the
  `axioms` region is empty).
- **Both model sides are diffed**, since the fold is a deep model and no
  `axiom_check.py` exists to cover the pure side: (a) the impl region's loop
  result, and (b) the postcondition's own witness
  `axis_count(ToSeq(shape), len(shape))` — the deep model of the patched
  `functools.reduce(lambda x,y: x*y, shape, 1)` (§2, row 3). Both must equal the
  real value on every input.
- **Oracle.** `ImmutableDenseNDimArray._new`'s `self._loop_size = …` assignment,
  `sympy/tensor/array/dense_ndim_array.py:152` (§1), **CALLED** — not
  transliterated. The gate applies the gold patch and sets `PYTHONPATH=/testbed`,
  so the patched function is imported and executed; nothing in the script
  reimplements it. `_assert_patched()` inspects the live source of `_new` and
  exits nonzero unless the patched `reduce(…, shape, 1)` form is present and the
  pre-patch `if shape else 0` form is gone. The value is read back two
  independent ways that must agree with each other and with the shadow:
  `arr._loop_size` (what the patched assignment stores) and `len(arr)`
  (`NDimArray.__len__`, ndim_array.py:164-178, the identity
  `return self._loop_size`), the latter whenever CPython's `__len__` protocol
  permits it (`0 <= n < 2**63`). Only the **Immutable** class is driven: the gold
  patch changes `ImmutableDenseNDimArray._new` alone and §1 binds the model
  there; `MutableDenseNDimArray._new` (:177) keeps the pre-patch expression, so
  diffing it would report a divergence outside the modeled unit.
- **Bridge (§2 inverted).** Model side `List[int]` axis lengths (`PSeq[int]` in
  the spec via `ToSeq`) → repo side `sympy.Tuple` of `_sympify`-ed `Integer`s:
  forward `ImmutableDenseNDimArray([], shape=tuple(shape))`, backward
  `int(arr._loop_size)`. The empty iterable is deliberate — `_loop_size` depends
  on `shape` alone, so no input costs O(product) memory and the domain is not
  quietly narrowed to shapes that fit in RAM. The bridge is **validated on every
  input**: `tuple(int(d) for d in arr.shape) == tuple(shape)` and
  `arr._rank == len(shape)`, so a constructor-normalized input can never be
  scored as agreement.
- **Inputs — 100000, pinned seed `SEED = 15017`.** The `Requires` is only
  `Acc(list_pred(shape), 1/2)` + `MustTerminate(2)`: it constrains the *list*,
  not the integers, so every `List[int]` is in the domain and none is filtered.
  That domain is infinite, so: (1) the F2P shapes built through the F2P test's
  own literal constructor calls (rank-0 `Array(x)`, `([], shape=(0,))`,
  `([23])`, `(range(3**4), (3,3,3,3))`, `Array(3)`) plus boundary shapes;
  (2) an **exhaustive** sweep of the finite sub-lattice rank 0..5 ×
  {-2,-1,0,1,2,3} — all 9331 shapes, every rank/sign/zero-placement combination
  in that box; (3) 90635 seeded fuzz inputs beyond it, including negative axis
  lengths and products past `__len__`'s index range (`2**62 * 3`, `10**6 ×
  10**6`) that the `Requires` admits and `_loop_size` still computes. Recorded
  coverage: rank-0 branch (zero loop iterations — the empty product, the bug
  under specification) 5432×, loop branch 94568×, `len()` cross-check 81124×;
  both `axis_count` cases (`k == 0` base, recursive step) exercised.
- **Recorded verdict.** `G-CONF=pass` — 100000 inputs, 0 disagreements.
- **Negative controls** (run out-of-tree under `/tmp`, confirming the check can
  fail): unpatched repo → `_assert_patched` refuses (exit 1); shadow paraphrased
  to the prepatch shape → AST tripwire fails (exit 1); same paraphrase with the
  tripwire disabled → the differential itself reports `shape=[]` shadow `0` vs
  real `1` (exit 1); bridge truncating the shape → round-trip validation fails
  (exit 1).
