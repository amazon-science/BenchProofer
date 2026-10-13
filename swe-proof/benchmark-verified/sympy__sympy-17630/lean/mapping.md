# mapping.md — sympy__sympy-17630

## Symbol binding (file:line @ base_commit 58e78209c8)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_matrixSum` / `problem_spec_matrixSum` / `correct_matrixSum` | the matrix-valued result returned by the `Add` constructor-postprocessor (`get_postprocessor(Add)._postprocessor`) on the all-matrix-terms branch | `sympy/matrices/expressions/matexpr.py:597-631` @ base_commit; the changed line is `matexpr.py:630` (the final `return`), guarded by the fix's new `matexpr.py:628a` (`if mat_class == MatAdd: return mat_class(*matrices).doit(deep=False)`) |
| `canonicalizeMatrixSum` | `MatAdd(*args).doit(deep=False)` → `canonicalize(MatAdd(*args))` | `sympy/matrices/expressions/matadd.py:70-76, 129-137` |
| `survivingNames` + `mergeSort nameLe` | the `rm_id(... ZeroMatrix)` + `sort(default_sort_key)` rules of `canonicalize` | `matadd.py:129-134` |

The modeled function is the `Add` postprocessor `_postprocessor(expr)`. When an
`Add` is constructed over a mix of matrix and non-matrix (scalar) terms, the
postprocessor partitions `expr.args` into `matrices` and `nonmatrices`. The
behavior the fix changes is the **all-matrix-terms** branch (`nonmatrices == []`,
`matrices != []`):

```python
        # ... (nonmatrices branch elided) ...
        # POST-PATCH (the fix adds these two lines):
        if mat_class == MatAdd:
            return mat_class(*matrices).doit(deep=False)
        # PRE-PATCH reached this line for Add too:
        return mat_class(cls._from_args(nonmatrices), *matrices).doit(deep=False)
```

With `nonmatrices == []`, `cls._from_args([])` is `S.Zero` (a **scalar**
`sympy.core.numbers.Zero`). So the pre-patch builds
`MatAdd(S.Zero, *matrices).doit(deep=False)`, prepending a scalar zero ahead of
the matrix terms. `MatAdd.doit` runs `canonicalize`, whose first rule
`rm_id(lambda x: x == 0 or isinstance(x, ZeroMatrix))` removes identity terms but
keeps the FIRST one when all are identities. When every matrix term is a
`ZeroMatrix` the retained first term is the scalar `S.Zero`, so the result is a
shapeless scalar `Zero` (no `.cols`/`.rows`/`.shape`). The fix's
`MatAdd(*matrices).doit(deep=False)` omits the scalar seed, so an all-zero sum
canonicalizes to a `ZeroMatrix` (shape preserved).

Observable: `type(b._blockmul(b).blocks[0,1])` is `Zero` (pre) vs `ZeroMatrix`
(post). The downstream `BlockMatrix.colblocksizes` reads `.cols` on that block;
a scalar `Zero` raises `AttributeError`, which is exactly the F2P crash
(`block_collapse(b*b*b)`).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| a term of the matrix-sum `args` that is a `ZeroMatrix` | `MatSumTerm.zeroMatrix` | the shaped additive-identity matrix |
| a term that is a named `MatrixSymbol(name, m, n)` | `MatSumTerm.named name` | `symbol.name` ↦ the Lean `String` |
| the scalar identity `S.Zero` seeded by `cls._from_args([])` (PRE-PATCH only) | `MatSumTerm.scalarZero` | the shapeless scalar zero injected ahead of the matrix terms |
| `MatAdd(*args).doit(deep=False)` is a `ZeroMatrix` | `MatSum.matrix []` | the (shaped) identity matrix; `names == []` |
| result is a `MatAdd` over named matrices, args in `default_sort_key` order | `MatSum.matrix [n₀, n₁, …]` | `[arg.name for arg in result.args]` ↦ the name list, codepoint-sorted |
| result is a single `MatrixSymbol` | `MatSum.matrix [name]` | a one-element name list |
| result is a scalar `sympy.core.numbers.Zero` (PRE-PATCH all-zero crash) | `MatSum.scalar` | the shape-losing degenerate outcome |

`default_sort_key` over distinct `MatrixSymbol` names coincides with codepoint
string order (validated empirically over 6000 random draws; G-CONF re-checks),
so `mergeSort nameLe` (`nameLe a b = decide (a ≤ b)`, Lean's `String ≤`) models
the canonical ordering.

## Domain restriction (preconditions)

`correct_matrixSum` is stated over inputs that are:
- non-empty (`terms ≠ []`): the postprocessor's all-matrix branch is only reached
  when `matrices` is non-empty (`if not matrices: return ...` returns earlier);
- free of `scalarZero` (`∀ t ∈ terms, t ≠ scalarZero`): the FIX never seeds a
  scalar identity into the matrix-term list — `scalarZero` models exactly the
  pre-patch injection, so the patched code's inputs to `canonicalizeMatrixSum`
  contain only `zeroMatrix`/`named` terms;
- name-distinct (`(survivingNames terms).Nodup`): real `MatAdd.doit` additionally
  combines like terms (`A + A → 2*A` via the `glom` rule), which is out of scope
  for this fix (the bug and its F2P tests involve only distinct symbols and zero
  blocks). Restricting to distinct names keeps the canonical form a pure
  drop-identities + sort, faithful to the F2P scenarios.

These are honest preconditions on the modeled branch, not a weakening of the
fixed behavior: the F2P tests (`test_issue_17624`, `test_zero_matrix_add`) all
fall inside this domain.

## Callee provenance + flag dependencies

- No callee axiom is consumed. The canonicalization (`MatAdd.doit` →
  `canonicalize`: drop identities, sort survivors) is the operation the fix's
  result flows through, modeled DEEPLY as `canonicalizeMatrixSum`; it is an
  A-reference validated by G-CONF against the real `Add(*terms)` postprocessor
  output, never axiomatized (§0.7).
- Flag dependency: the changed branch is reached only for `mat_class == MatAdd`
  (`cls == Add`) with `nonmatrices == []` and `matrices != []`. G-CONF fuzzes
  exactly this configuration: `Add(*matrix_terms)` over `MatrixSymbol`/`ZeroMatrix`
  terms only.

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).
