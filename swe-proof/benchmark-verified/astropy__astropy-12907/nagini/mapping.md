# mapping.md — astropy__astropy-12907

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d16bfe05a744909de4b27f5875fe0d4ed41ce607`, states the type
abstraction, and records callee provenance.

Repo file under change: `astropy/modeling/separable.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `parallel_dependency_matrix(left, right, lr, lc, rr, rc)` | `_cstack(left, right)` — `astropy/modeling/separable.py:219` (changed body line 245) | the modeled changed function: the `'&'`-operator combiner that stacks two coord/separability matrices side by side |
| `expected_row(left, right, lr, lc, rr, rc, i)` | the per-row content of `np.hstack([cleft, cright])` where `cleft`/`cright` are the zero-padded block placements built in `_cstack` (lines 239-247) | pure spec: the i-th row of the stacked matrix |
| `zeros(n)` | the `np.zeros((noutp, …))` padding that surrounds each block (lines 239, 244) | pure spec: a zero padding block |
| `is_grid(m, rows, cols)` | the array-shape contract `m.shape == (rows, cols)` for the 0/1 coord matrices | pure spec: matrix well-formedness |

The single changed line (gold patch):

```
-        cright[-right.shape[0]:, -right.shape[1]:] = 1
+        cright[-right.shape[0]:, -right.shape[1]:] = right
```

is the `else` branch of `_cstack` taken when `right` is already a coordinate
matrix (an `ndarray`), i.e. when the right child of the `&` operation is itself
a (compound) transform whose separability matrix has already been computed —
the nested-CompoundModel case from the problem statement. The block being
assigned, `cright[-right.shape[0]:, -right.shape[1]:]`, is exactly the
lower-right `rr x rc` block of `cright`; `right.shape[1] == cright.shape[1]`
so the column slice spans the whole width of `cright` and the row slice spans
its last `rr = right.shape[0]` rows.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a 2-D `numpy.ndarray` of 0/1 floats (a coord/separability matrix), shape `(r, c)` | `PSeq[PSeq[int]]` with extents `r`, `c` (`is_grid(m, r, c)`) | `m[i, j]` ↔ `m[i][j]`; `m.shape[0]` ↔ `r`, `m.shape[1]` ↔ `c`; `np.hstack` of row-aligned blocks ↔ per-row `PSeq` concatenation; `np.vstack`/row stacking ↔ outer `PSeq` concatenation |
| `0.0` / `1.0` array entries (booleanised later by `separability_matrix`: `!= 0 → True`) | `0` / `1` ints | the separability test only reads whether each entry is zero vs nonzero; integers `0`/`1` are an exact, precision-independent stand-in (the patch introduces no arithmetic, only a copy, so no float precision is involved) |
| `left, right` parameters of `_cstack` in the `ndarray` branches | `left, right : PSeq[PSeq[int]]` (read-only) | the function reads the blocks and stacks them; it does not mutate the inputs. Pure sequences are immutable, so read-only-ness is automatic (no `list_pred` permission to leak through a postcondition — directive 5 satisfied vacuously by the pure carrier) |
| `noutp = _compute_n_outputs(left, right) = left.shape[0] + right.shape[0]` (line 234, via `_compute_n_outputs`) | `noutp = lr + rr` | the result has `lr + rr` rows |
| the result width `cleft.shape[1] + cright.shape[1] = lc + rc` | `lc + rc` | the result has `lc + rc` columns |

### 2.1 Why the model covers exactly the patched branch

`_cstack` has four sub-cases (`left` Model/ndarray × `right` Model/ndarray).
The gold patch changes only the **`right` is an ndarray** sub-case (lines
244-245). The model's `parallel_dependency_matrix` takes both `left` and
`right` as already-computed matrices (the ndarray×ndarray shape), which is the
shape in which the bug manifests — both children of the outer `&` have already
been reduced to coord matrices, as happens for `m.Pix2Sky_TAN() & cm` and the
new F2P models `rot & (sh1 & sh2)` / `rot & sh1 & (scl1 & scl2)`. The upper
block (`cleft[:lr,:lc] = left`, line 240, the `left`-is-ndarray branch) is
modeled identically (`left[i] + zeros(rc)`); it is unchanged by the patch and
serves as the I-tagged context for the lower block whose fill is the fix.

## 3. Callee provenance

No `@ContractOnly` axiom is used: the combination is pure block placement
(zero-padding + copying the operands), modeled **deeply** over `PSeq` and
pinned element/row-exactly by the spec. The only library operations the patched
hunk performs — `np.zeros`, slice assignment, `np.hstack` — are linear-algebra
block placement with no behavioural subtlety beyond "copy the operand into the
block", which is precisely what `expected_row`'s concatenation encodes. There
is therefore no unchanged opaque callee to axiomatize and no A-reference deep
model to validate against a real library function: the whole operation is
expressed directly. `axiom_check.py` instead exercises the block-placement
semantics against a direct numpy re-implementation of the gold `_cstack` branch
(boundary + fuzz) to confirm the model's row layout equals the real array
layout the patch produces.
