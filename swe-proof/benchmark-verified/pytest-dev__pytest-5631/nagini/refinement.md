# refinement.md — pytest-dev__pytest-5631

The operation-by-operation correspondence between `model.py`'s implementation
(the `count_mock_patch_args` impl region and the deep model
`counts_as_mock` / `count_sentinel_directives`) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == real runtime semantics by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The counting site — `num_mock_patch_args()` (`src/_pytest/compat.py:62`)

Gold hunk (pre → post):
```
- mock_modules = [sys.modules.get("mock"), sys.modules.get("unittest.mock")]
- if any(mock_modules):
-     sentinels = [m.DEFAULT for m in mock_modules if m is not None]
-     return len([p for p in patchings if not p.attribute_name and p.new in sentinels])
- return len(patchings)
+ mock_sentinel = getattr(sys.modules.get("mock"), "DEFAULT", object())
+ ut_mock_sentinel = getattr(sys.modules.get("unittest.mock"), "DEFAULT", object())
+ return len([p for p in patchings
+     if not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)])
```

| # | model.py impl op (`count_mock_patch_args`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `kinds: List[int]` | `function.patchings` (sequence of `_patch` directives) | R | `patchings` ↔ `List[int]` of per-directive kind tags (mapping.md §2); each element abstracts the only two attributes the helper reads, `p.attribute_name` and `p.new`. |
| A2 | the early `len(kinds)==0` case folded into the loop / fold (empty → count 0) | `if not patchings: return 0` | R + I | an empty directive sequence yields count 0; `count_sentinel_directives` returns 0 on the empty sequence and the loop body never runs. Observationally identical. |
| A3 | per-directive decision `counts_as_mock(c)` = `(c == 1)`, i.e. "binds no attribute name AND value is a placeholder singleton by identity" | `not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)` | A-reference | the changed membership operation is modelled **deeply**: `counts_as_mock`/`count_sentinel_directives` ARE the per-directive identity decision and its count. There is **no consumed `@ContractOnly` axiom** — the proof depends on none. The deep model is validated **== the real runtime semantics** out-of-band: G-AX (axiom_check.py) builds real directives over the real `unittest.mock.DEFAULT` placeholder singleton and asserts the identity decision is total + exact and the model count equals the real identity count. `is` is identity comparison (mapping.md §3.1), which is the total decision kind 1 ⇔ `p.new is <sentinel>` encodes. |
| A4 | the loop accumulates `count` and returns it; `count == count_sentinel_directives(ToSeq(kinds))` | `return len([p for p in patchings if <predicate>])` | R + I | the model's backward fold computes exactly the size of the sublist satisfying the per-directive predicate; `len([... if predicate])` is that same count. Type-refined from `List[int]` kinds to the real directive list. |

The discriminating content of the change — **identity (`is`) instead of
value-equality (`in`/`==`)** — lives in `counts_as_mock` being TOTAL (a definite
boolean for every kind, including kind 3) ⇔ the post-patch `p.new is <sentinel>`
never invoking `__eq__`. The pre-patch used value-equality membership
`p.new in sentinels`, which raises on an array-like `p.new`;
`model_prepatch.py` reproduces that (a `raise NonTruthEvaluableEquality()` on
kind 3) and **fails** the totality clause of the contract (no `Exsures`),
which is exactly the spec sensing the change (G-DIFF; the verifier reports
"method raises no exceptions might not hold").

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the membership decision (value-equality → identity) — is modelled
**deeply** (the total per-directive classifier `counts_as_mock` and the fold
`count_sentinel_directives`, step A3, an **A-reference**), not hidden behind an
axiom about the function under change. There is **no consumed axiom**:
`unittest.mock.DEFAULT` is a runtime singleton, not a callee whose contract the
proof consumes; the identity operator `is` is a primitive Nagini expresses
directly (here as kind-tag equality). The escape from "spec too weak" is the
**totality** obligation (no `Exsures`): the spec demands a count be produced for
EVERY admissible input, which the value-equality skeleton cannot deliver on a
kind-3 directive.

## C. verify(model) ⇒ resolved

`count_mock_patch_args` verifies only if (i) it returns the exact count of
no-attribute identity-placeholder directives (`Result() ==
count_sentinel_directives(ToSeq(kinds))`, step A4) AND (ii) it raises nothing on
ANY admissible input, including a kind-3 directive (the totality clause). By R
(directive ↔ kind tag, `patchings` ↔ `List[int]`) the verified counter equals
`len([p for p in patchings if not p.attribute_name and (p.new is mock_sentinel
or p.new is ut_mock_sentinel)])` on the directive populations the tests build;
by G-AX the deep model equals the real identity decision (A-reference) — total
and exact on the real `unittest.mock.DEFAULT`. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited identity semantics — and the gold patch resolves (G-RESOLVE):
`test_mock_sentinel_check_against_numpy_like` collects without the pre-patch
`ValueError`, and the existing mock-decoration tests (P2P) keep counting the
same arguments. The trust point reduces to the single A-reference (G-AX) plus
refinement fidelity (this document, G-EQ).
