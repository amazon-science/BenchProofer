# refinement.md — pydata__xarray-3151

The operation-by-operation correspondence between `model.py`'s implementation
(the `guard_rejects` impl region + the deep `any_joined_nonmonotonic` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee/behaviour by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The guard site — `combine_by_coords` (`xarray/core/combine.py:503-511`)

Gold hunk:
```
- for dim in concatenated.dims:
-     if dim in concatenated:
-         indexes = concatenated.indexes.get(dim)
-         if not (indexes.is_monotonic_increasing
-                 or indexes.is_monotonic_decreasing):
-             raise ValueError("Resulting object does not have monotonic"
-                              " global indexes along dimension {}"
-                              .format(dim))
+ for dim in concat_dims:
+     indexes = concatenated.indexes.get(dim)
+     if not (indexes.is_monotonic_increasing
+             or indexes.is_monotonic_decreasing):
+         raise ValueError("Resulting object does not have monotonic"
+                          " global indexes along dimension {}"
+                          .format(dim))
```

| # | model.py impl op (`guard_rejects`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `is_joined: List[int]`, `is_monotonic: List[int]` (parallel 0/1 flags, one per coordinate dimension present in the result) | the implicit per-dimension metadata of `concatenated`: `concat_dims` membership and each dimension's `is_monotonic_increasing or is_monotonic_decreasing` | R | `dim in concat_dims` ↔ `is_joined[d] == 1`; the single-coordinate monotonicity test ↔ `is_monotonic[d] == 1` (mapping.md §2). The rich `Dataset`/`Index` carrier reduces to two boolean flags per dimension. |
| A2 | the loop iterates every position `d` and acts only when `is_joined[d] == 1` | post-patch `for dim in concat_dims:` (iterates exactly the joined dimensions) | R | `concat_dims` is precisely `{ d : is_joined[d] == 1 }` (mapping.md §3.1 — a dim is appended to `concat_dims` only when its coordinate varies between inputs). Iterating `concat_dims` ↔ acting only on the `is_joined == 1` positions. |
| A3 | `if is_monotonic[i-1] == 0: rejected = True` | `indexes = concatenated.indexes.get(dim); if not (indexes.is_monotonic_increasing or indexes.is_monotonic_decreasing): raise ValueError(...)` | R + A-reference | the per-coordinate monotonicity test (increasing OR decreasing) is an unchanged predicate whose boolean outcome is the carrier flag `is_monotonic` (R). The overall guard outcome — `Result()` true iff some joined dim is non-monotonic — is the changed selection modelled **deeply** as `any_joined_nonmonotonic` (A-reference): there is no consumed axiom; G-AX validates `any_joined_nonmonotonic == real post-patch guard` (mapping.md §3.1). |
| A4 | `return rejected` (a `bool`; `True` = guard rejects) | `raise ValueError(...)` vs. falling through to `concatenated_grouped_by_data_vars.append(concatenated)` | R | raising ↔ `Result() == True`; completing the loop ↔ `Result() == False` (mapping.md §2). The appended `concatenated` and the downstream `merge` are unchanged by the guard and outside the modeled behaviour. |
| A5 | `Requires(MustTerminate(2))` + the loop measure `Invariant(MustTerminate(i))` | the real guard is a bounded `for` loop over the finite `concat_dims`; it always completes (raising or falling through) | R | total-correctness obligation: the real guard always ANSWERS. Nagini is a partial-correctness verifier by default, so without the obligation a non-terminating impl (no normal exit) satisfies every value `Ensures` vacuously — the spec-too-weak hole the G-PANEL-1 audit exploited (its `atk4_oracle_echo` witness verified with an unreachable return). A diverging guard would hang `combine_by_coords` and the F2P test, so it does not resolve. |

The discriminating content of the change — the guard inspects only the
**joined** dimensions (`concat_dims`) rather than **all coordinate** dimensions
present in the result (`concatenated.dims` filtered by `dim in concatenated`) —
lives in the `is_joined[i-1] == 1` test of `guard_rejects` (model) ⇔ the
`for dim in concat_dims` head of the post-patch loop (real). The pre-patch loop
inspected every coordinate dimension present; `model_prepatch.py` reproduces
that (it drops the `is_joined` guard and rejects on any non-monotonic dimension)
and **fails** the loop invariant
`rejected == any_joined_nonmonotonic(...)`, which is exactly the spec sensing
the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely
*changed* — the set of dimensions the monotonicity guard inspects — is modelled
**deeply** (the spelled-out front-recursive existential `any_joined_nonmonotonic`
consumed in `guard_rejects`, step A3, an **A-reference**), not hidden behind an
axiom about the function under change. There is **no consumed `@ContractOnly`
axiom** in this bundle: the unchanged single-coordinate monotonicity test and
the unchanged join machinery (`_infer_concat_order_from_coords`, `_combine_nd`,
`merge`) are type/refinement boundaries (R), documented in mapping.md, not
axioms. The empty `axioms` region reflects this.

## C. verify(model) ⇒ resolved

`guard_rejects` verifies only if its result equals
`any_joined_nonmonotonic(is_joined, is_monotonic)` — i.e. it rejects exactly
when some **joined** dimension is non-monotonic and never on account of a
carried-through (bystander) dimension (A3). By R (the `concat_dims ⟺ is_joined`
and monotonicity-test ⟺ `is_monotonic` bijections, raise ⟺ `Result() == True`),
the verified guard equals the post-patch `for dim in concat_dims: ... raise`
loop on the tested inputs; by G-AX the deep model `any_joined_nonmonotonic`
equals the real post-patch guard (A-reference), including the real
`combine_by_coords` on the issue's non-monotonic-bystander scenario. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and an audited deep model — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: there is no
consumed axiom (so axiom soundness is vacuous beyond the A-reference G-AX check)
and refinement fidelity (this document, G-EQ).
